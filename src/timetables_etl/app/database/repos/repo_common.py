"""
Instead of having try/except blocks for each repo call, define a decorator to handle it
"""

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Generic, ParamSpec, Type, TypeAlias, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from structlog.stdlib import get_logger

from ..client import BodsDB

logger = get_logger()


T = TypeVar("T")
P = ParamSpec("P")


DBModelT = TypeVar("DBModelT")


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


def get_operation_name(func: Callable, args: tuple[Any, ...]) -> str:
    """Safely extract operation name from args"""
    try:
        instance = args[0] if args else None
        return (
            f"{instance.__class__.__name__}.{func.__name__}"
            if instance
            else func.__name__
        )
    except Exception:
        return func.__name__


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
    except Exception as e:
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
        operation = get_operation_name(func, args)
        log = logger.bind(operation=operation)

        try:
            result = func(*args, **kwargs)
            log.debug("repository.operation.success")
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


class BaseRepository(Generic[DBModelT]):
    """
    Base repository with common CRUD operations.
    """

    def __init__(self, db: BodsDB, model: Type[DBModelT]):
        self._db = db
        self._model = model
        self._log = logger.bind(
            repository=self.__class__.__name__, model=model.__name__
        )

    def _build_query(self) -> Select:
        """Build base query for the model"""
        return select(self._model)

    @handle_repository_errors
    def _fetch_one(self, statement: Select) -> DBModelT | None:
        with self._db.session_scope() as session:
            result = session.execute(statement).scalar_one_or_none()
            if result:
                session.expunge(result)
            return result

    @handle_repository_errors
    def _fetch_all(self, statement: Select) -> list[DBModelT]:
        with self._db.session_scope() as session:
            results = list(session.execute(statement).scalars().all())
            for result in results:
                session.expunge(result)
            return results

    @handle_repository_errors
    def _update_one(
        self, statement: Select, update_func: Callable[[DBModelT], None]
    ) -> None:
        """Execute an update on a single record"""
        with self._db.session_scope() as session:
            record = session.execute(statement).scalar_one()
            update_func(record)
            session.merge(record)

    @handle_repository_errors
    def _execute_update(
        self, callback: Callable[[DBModelT], None], statement: Select
    ) -> None:
        with self._db.session_scope() as session:
            record = session.execute(statement).scalar_one()
            callback(record)
            session.merge(record)

    @handle_repository_errors
    def get_all(self) -> list[DBModelT]:
        """Get all entities"""
        with self._db.session_scope() as session:
            statement = self._build_query()
            return list(session.execute(statement).scalars().all())

    @handle_repository_errors
    def update(self, record: DBModelT) -> None:
        """Update entity"""
        with self._db.session_scope() as session:
            try:
                session.merge(record)
            except Exception:
                logger.error("Could not update data")
                raise

    @handle_repository_errors
    def insert(self, record: DBModelT) -> DBModelT:
        """
        Insert a single record and return it with generated ID
        """
        self._log.debug("Inserting Single Record", record_type=type(record).__name__)
        with self._db.session_scope() as session:
            session.add(record)
            session.flush()
            session.expunge(record)
            self._log.debug("Record Insert Sucess")
            return record

    @handle_repository_errors
    def bulk_insert(self, records: list[DBModelT]) -> list[DBModelT]:
        """
        Insert multiple records and return them with generated IDs
        flush() may be needed to ensure IDs are generated
        """
        self._log.debug("Bulk inserting records", record_count=len(records))
        with self._db.session_scope() as session:
            for record in records:
                session.add(record)
            session.flush()
            results = list(records)
            for result in results:
                session.expunge(result)
            self._log.debug("Bulk inserting completed", inserted_count=len(results))
            return results
