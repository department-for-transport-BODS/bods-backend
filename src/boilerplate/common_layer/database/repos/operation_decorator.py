"""
Decorator that handles DB Errors and Debug Logging
"""

import inspect
import json
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeAlias, TypeVar

from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from structlog.stdlib import BoundLogger, get_logger

logger = get_logger()
T = TypeVar("T")
P = ParamSpec("P")


class SQLDBClientError(Exception):
    """Base class for repository exceptions"""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        self.error_locations: list[dict[str, str | int]] = []

        try:
            frame_info = inspect.stack()[2]  # Skip the decorator frame
            location = {
                "File": frame_info.filename,
                "Line": frame_info.lineno,
                "Function": frame_info.function,
            }
            self.filename = frame_info.filename
            self.line = frame_info.lineno
            self.function = frame_info.function
            self.error_locations.append(location)
        except (IndexError, AttributeError):
            location = {
                "File": "<unknown>",
                "Line": 0,
                "Function": "<unknown>",
            }
            self.filename = "<unknown>"
            self.line = 0
            self.function = "<unknown>"
            self.error_locations.append(location)

        if isinstance(original_error, SQLDBClientError):
            self.error_locations.extend(original_error.error_locations)

        super().__init__(self.message)

    def __str__(self) -> str:
        """Format the exception as a JSON string"""
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        """Convert the exception details to a structured dictionary"""
        error_dict: dict[str, Any] = {
            "ErrorType": self.__class__.__name__,
            "Message": self.message,
            "Locations": self.error_locations,
        }

        # Get the actual root cause, not another SQLDBClientError
        root_error = self.original_error
        while isinstance(root_error, SQLDBClientError) and root_error.original_error:
            root_error = root_error.original_error

        if root_error and not isinstance(root_error, SQLDBClientError):
            original_error_info: dict[str, Any] = {
                "Type": root_error.__class__.__name__,
                "Message": str(root_error),
            }

            # Add SQLAlchemy specific details if applicable
            if isinstance(root_error, SQLAlchemyError):
                sql_info: dict[str, Any] = {}
                stmt = getattr(root_error, "statement", None)
                if stmt is not None:
                    sql_info["Statement"] = str(stmt)

                params = getattr(root_error, "params", None)
                if params is not None:
                    sql_info["Parameters"] = str(params)

                if sql_info:
                    original_error_info["SQLDetails"] = sql_info

            error_dict["OriginalError"] = original_error_info

        return error_dict


class SQLDBNotFoundError(SQLDBClientError):
    """Raised when an entity is not found"""


class SQLDBUpdateError(SQLDBClientError):
    """Raised when an update operation fails"""


ErrorMapping: TypeAlias = dict[type[Exception], tuple[type[SQLDBClientError], str]]


def get_operation_name(
    func: Callable[..., Any], args: tuple[Any, ...]
) -> tuple[str | None, str]:
    """
    Safely extract repository and operation names
    Returns: (repository_name, operation_name)
    """
    try:
        instance = args[0] if args else None
        is_class_instance = (
            instance is not None
            and hasattr(instance, "__class__")
            and not isinstance(instance.__class__, type)
        )
        repo_name = instance.__class__.__name__ if is_class_instance else None
        return repo_name, func.__name__
    except AttributeError:
        return None, func.__name__


def extract_error_details(exc: Exception) -> tuple[str, dict[str, Any]]:
    """Safely extract error details from exception"""
    try:
        if isinstance(exc, SQLAlchemyError):
            error_msg = str(exc).split("\n", maxsplit=1)[0]
            return error_msg, {
                "sql_statement": str(getattr(exc, "statement", "")),
                "sql_params": str(getattr(exc, "params", {})),
            }
        return str(exc), {}
    except Exception as e:  # pylint: disable=broad-exception-caught
        return f"Error extracting details: {str(e)}", {}


def get_operation_logger(instance: Any | None, func: Callable[..., Any]) -> BoundLogger:
    """
    Get appropriate logger for repository operation
    Multiple Fallbacks to ensure that it won't cause a crash or None
    """
    log = logger
    try:
        # First try: Get repository's pre-configured logger
        if hasattr(instance, "_log"):
            if instance is not None:
                log = instance._log  # pylint: disable=protected-access
        # Second try: Create logger with repository name from instance
        elif instance and hasattr(instance, "__class__"):
            log = logger.bind(repository=instance.__class__.__name__)

        # Always bind the operation name regardless of which logger we're using
        return log.bind(operation=func.__name__)

    except Exception:  # pylint: disable=broad-exception-caught
        return logger.bind(operation=func.__name__)


def handle_repository_errors(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to handle common repository exceptions
    To reduce try / except blocks for repo actions
    """
    error_mapping: ErrorMapping = {
        NoResultFound: (SQLDBNotFoundError, "Resource not found"),
        IntegrityError: (SQLDBUpdateError, "Database integrity error"),
        SQLAlchemyError: (SQLDBClientError, "Database error"),
    }

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        instance = args[0] if args else None
        log = get_operation_logger(instance, func)

        try:
            result = func(*args, **kwargs)
            log.debug("Database Operation Successful")
            return result

        except Exception as exc:
            error_msg = str(exc).split("\n", maxsplit=1)[0]
            error_details = {
                "error": str(exc.__class__.__name__),
                "error_details": str(error_msg),
            }

            if isinstance(exc, SQLAlchemyError):
                error_details.update(
                    {
                        "sql_statement": str(getattr(exc, "statement", "")),
                        "sql_params": str(getattr(exc, "params", {})),
                    }
                )

            log_event = log.bind(**error_details)

            for exc_type, (error_class, message) in error_mapping.items():
                if isinstance(exc, exc_type):
                    log_event.error(f"repository.operation.{exc_type.__name__.lower()}")
                    raise error_class(message=message, original_error=exc) from exc

            log_event.error("repository.operation.unexpected")
            raise SQLDBClientError(
                message="Unexpected error", original_error=exc
            ) from exc

    return wrapper
