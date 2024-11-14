"""
Instead of having try/except blocks for each repo call, define a decorator to handle it
"""

import logging
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Generic, ParamSpec, Type, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from ..client import BodsDB

logger = logging.getLogger(__name__)


T = TypeVar("T")
P = ParamSpec("P")


logger = logging.getLogger(__name__)

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


def handle_repository_errors(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to handle common repository exceptions.
    Reduces duplicate try / except
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if args and hasattr(args[0], "__class__"):
            class_name = args[0].__class__.__name__
            operation = f"{class_name}.{func.__name__}"
        else:
            operation = func.__name__

        try:
            return func(*args, **kwargs)
        except Exception as exc:  # noqa
            match exc:
                case NoResultFound():
                    message = f"Failed in {operation}: Resource not found"
                    logger.exception(message)
                    raise NotFoundError(message=message, original_error=exc) from exc
                case IntegrityError():
                    message = f"Failed in {operation}: Database integrity error"
                    logger.exception(message)
                    raise UpdateError(message=message, original_error=exc) from exc
                case SQLAlchemyError():
                    message = f"Failed in {operation}: Database error"
                    logger.exception(message)
                    raise RepositoryError(message=message, original_error=exc) from exc
                case _:
                    message = f"Failed in {operation}: Unexpected error"
                    logger.exception(message)
                    raise RepositoryError(message=message, original_error=exc) from exc

    return wrapper


class BaseRepository(Generic[DBModelT]):
    """
    Base repository with common CRUD operations.
    """

    def __init__(self, db: BodsDB, model: Type[DBModelT]):
        self._db = db
        self._model = model

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
