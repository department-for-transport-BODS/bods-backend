"""
SQL Alchemy Repos for Tables prefixed with data_quality_
"""

from datetime import UTC, datetime

from structlog.stdlib import get_logger

from ..client import SqlDB
from ..models import (
    DataQualityPostSchemaViolation,
    DataQualityPTIObservation,
    DataQualityPTIValidationResult,
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


def create_violation_from_parse_error(
    exc: Exception, revision_id: int, filename: str
) -> DataQualitySchemaViolation:
    """
    Create a DataQualitySchemaViolation from a parse error (XMLSyntaxError or similar).
    Uses defensive getattr because not all exceptions have .lineno or .msg.
    """
    line_number = getattr(exc, "lineno", None)
    message = getattr(exc, "msg", None)

    return DataQualitySchemaViolation(
        filename=filename,
        line=line_number if isinstance(line_number, int) else 0,
        details=message if isinstance(message, str) else str(exc),
        created=datetime.now(UTC),
        revision_id=revision_id,
    )


def add_schema_violations_to_db(
    db: SqlDB, violations: list[DataQualitySchemaViolation]
) -> list[DataQualitySchemaViolation]:
    """
    Add Schema Violations Found to Database
    """
    if not violations:
        logger.info("No Violations found. Skipping Database Insert of Violations")
        return []
    logger.info("Adding Violations to DB", count=len(violations))
    result = DataQualitySchemaViolationRepo(db).bulk_insert(violations)
    logger.info("Successfully added violations to DB", count=len(result))
    return result


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
        Retrieve all DataQualityPostSchemaViolation for a specific revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)


class DataQualityPTIValidationResultRepo(
    BaseRepositoryWithId[DataQualityPTIValidationResult]
):
    """
    Data Quality PTI Validation Result
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, DataQualityPTIValidationResult)

    @handle_repository_errors
    def get_by_revision_id(
        self, revision_id: int
    ) -> DataQualityPTIValidationResult | None:
        """
        Retrieve all DataQualityPTIValidationResult for a specific revision
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_first(statement)
