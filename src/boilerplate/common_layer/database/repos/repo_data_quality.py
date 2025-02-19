"""
SQL Alchemy Repos for Tables prefixed with data_quality_
"""

from structlog.stdlib import get_logger

from ..client import SqlDB
from ..models.model_data_quality import (
    DataQualityPostSchemaViolation,
    DataQualityPTIObservation,
    DataQualitySchemaViolation,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepositoryWithId

logger = get_logger()


class DataQualitySchemaViolationRepo(BaseRepositoryWithId[DataQualitySchemaViolation]):
    """Repository for managing Data Quality Schema Violation entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, DataQualitySchemaViolation)

    @handle_repository_errors
    def get_by_revision_id(
        self, revision_id: int
    ) -> list[DataQualitySchemaViolation] | None:
        """
        Retrieve all DataQualityPostSchemaViolation for a specific revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def delete_by_revision_id(self, revision_id: int) -> int:
        """
        Delete all DataQualitySchemaViolations for a specific revision

        Returns: number of deleted records
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._delete_all(statement)


class DataQualityPostSchemaViolationRepo(
    BaseRepositoryWithId[DataQualityPostSchemaViolation]
):
    """Repository for managing Data Quality Post Schema Violation entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, DataQualityPostSchemaViolation)

    @handle_repository_errors
    def get_by_revision_id(
        self, revision_id: int
    ) -> list[DataQualityPostSchemaViolation] | None:
        """
        Retrieve all DataQualityPostSchemaViolation for a specific revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def delete_by_revision_id(self, revision_id: int) -> int:
        """
        Delete all DataQualityPostSchemaViolations for a specific revision

        Returns: number of deleted records
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._delete_all(statement)


class DataQualityPTIObservationRepo(BaseRepositoryWithId[DataQualityPTIObservation]):
    """
    DataQuality PTI Observation
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, DataQualityPTIObservation)

    @handle_repository_errors
    def get_by_revision_id(
        self, revision_id: int
    ) -> list[DataQualityPTIObservation] | None:
        """
        Retrieve all DataQualityPTIObservations for a specific revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def delete_by_revision_id(self, revision_id: int) -> int:
        """
        Delete all DataQualityPTIObservations for a specific revision

        Returns: number of deleted records
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._delete_all(statement)
