"""
Decorator that handles DB Errors and Debug Logging
"""

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeAlias, TypeVar

from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from structlog.stdlib import get_logger

logger = get_logger()
T = TypeVar("T")
P = ParamSpec("P")


@dataclass
class RepositoryError(Exception):
    """Base class for repository exceptions"""

    message: str
    original_error: Exception | None = None


class NotFoundError(RepositoryError):
    """Raised when an entity is not found"""


class UpdateError(RepositoryError):
    """Raised when an update operation fails"""


ErrorMapping: TypeAlias = dict[type[Exception], tuple[type[RepositoryError], str]]


def get_operation_name(func: Callable, args: tuple[Any, ...]) -> tuple[str | None, str]:
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


def handle_repository_errors(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to handle common repository exceptions
    To reduce try / except blocks for repo actions
    """
    error_mapping: ErrorMapping = {
        NoResultFound: (NotFoundError, "Resource not found"),
        IntegrityError: (UpdateError, "Database integrity error"),
        SQLAlchemyError: (RepositoryError, "Database error"),
    }

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        repo_name, operation = get_operation_name(func, args)
        log = logger.bind(repo=repo_name, operation=operation)

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
            raise RepositoryError(
                message="Unexpected error", original_error=exc
            ) from exc

    return wrapper
