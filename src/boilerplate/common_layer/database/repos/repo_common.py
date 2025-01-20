"""
Instead of having try/except blocks for each repo call, define a decorator to handle it
"""

from typing import (
    Callable,
    Generic,
    Protocol,
    Sequence,
    Type,
    TypeVar,
    runtime_checkable,
)

from sqlalchemy import Column, Select, delete, select
from structlog.stdlib import get_logger

from ..client import SqlDB
from ..models.common import BaseSQLModel
from .operation_decorator import handle_repository_errors

logger = get_logger()


DBModelT = TypeVar("DBModelT", bound=BaseSQLModel)


@runtime_checkable
class HasId(Protocol):
    """
    A Protocol to check if the table using BaseRepositoryWithId has an Id column
    If there isn't an ID column the Repo should inherit from BaseRepository
    """

    id: Column[int]


class BaseRepository(Generic[DBModelT]):
    """
    Base repository with common CRUD operations.
    """

    def __init__(self, db: SqlDB, model: Type[DBModelT]):
        self._db = db
        self._model = model
        self._log = logger.bind(
            repository=self.__class__.__name__, model=model.__name__
        )

    def _build_query(self) -> Select[tuple[DBModelT]]:
        """Build base query for the model"""
        return select(self._model)

    @handle_repository_errors
    def _fetch_one(self, statement: Select[tuple[DBModelT]]) -> DBModelT | None:
        with self._db.session_scope() as session:
            result = session.execute(statement).scalar_one_or_none()
            if result:
                session.expunge(result)
            return result

    @handle_repository_errors
    def _fetch_all(self, statement: Select[tuple[DBModelT]]) -> list[DBModelT]:
        with self._db.session_scope() as session:
            results = list(session.execute(statement).scalars().all())
            for result in results:
                session.expunge(result)
            return results

    @handle_repository_errors
    def _update_one(
        self,
        statement: Select[tuple[DBModelT]],
        update_func: Callable[[DBModelT], None],
    ) -> None:
        """Execute an update on a single record"""
        with self._db.session_scope() as session:
            record = session.execute(statement).scalar_one()
            update_func(record)
            session.merge(record)

    @handle_repository_errors
    def _execute_update(
        self, callback: Callable[[DBModelT], None], statement: Select[tuple[DBModelT]]
    ) -> None:
        with self._db.session_scope() as session:
            record = session.execute(statement).scalar_one()
            callback(record)
            session.merge(record)

    @handle_repository_errors
    def get_all(self) -> list[DBModelT]:
        """
        Get all rows in a table
        """
        statement = select(self._model)
        with self._db.session_scope() as session:
            results: Sequence[DBModelT] = session.execute(statement).scalars().all()
            for result in results:
                session.expunge(result)
            return list(results)

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
            self._log.debug("Record Insert Success")
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


class BaseRepositoryWithId(BaseRepository[DBModelT]):
    """
    Base repository for models that have an 'id' primary key.
    Extends BaseRepository with common ID-based operations.
    """

    @handle_repository_errors
    def get_by_id(self, id_column_id: int) -> DBModelT | None:
        """Get entity by ID"""
        if not isinstance(self._model, HasId):
            raise TypeError(f"Model {self._model.__name__} must have an 'id' field")
        statement = self._build_query().where(self._model.id == id_column_id)
        return self._fetch_one(statement)

    @handle_repository_errors
    def get_by_ids(self, ids: list[int]) -> list[DBModelT]:
        """Get multiple entities by their IDs"""
        if not isinstance(self._model, HasId):
            raise TypeError(f"Model {self._model.__name__} must have an 'id' field")
        if not ids:
            return []
        statement = self._build_query().where(self._model.id.in_(ids))
        return self._fetch_all(statement)

    @handle_repository_errors
    def delete_by_id(self, id_column_id: int) -> bool:
        """
        Delete a single record by the given ID.

        Returns:
            bool: True if the record was deleted, False otherwise.
        """
        if not isinstance(self._model, HasId):
            raise TypeError(
                f"Model {self._model.__name__} must have an 'id' field to delete by id"
            )

        with self._db.session_scope() as session:
            statement = delete(self._model).where(  # pyright: ignore
                self._model.id == id_column_id
            )
            result = session.execute(statement)
            return result.rowcount > 0
