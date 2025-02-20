"""
Database Operations for Schema Check
"""

from datetime import UTC, datetime

from common_layer.database.client import SqlDB
from common_layer.database.models.model_data_quality import DataQualitySchemaViolation
from common_layer.database.repos.repo_data_quality import DataQualitySchemaViolationRepo
from lxml.etree import _LogEntry  # type: ignore
from structlog.stdlib import get_logger

log = get_logger()


def create_violation_from_error(
    error: _LogEntry, revision_id: int, filename: str
) -> DataQualitySchemaViolation:
    """
    Create a DataQualitySchemaViolation instance from an lxml error
    """
    return DataQualitySchemaViolation(
        filename=filename,
        line=error.line,
        details=error.message,
        created=datetime.now(UTC),
        revision_id=revision_id,
    )


def add_violations_to_db(
    db: SqlDB, violations: list[DataQualitySchemaViolation]
) -> list[DataQualitySchemaViolation]:
    """
    Add Schema Violations Found to Database
    """
    if len(violations) == 0:
        log.info("No Violations found. Skipping Database Insert of Violations")
        return []
    log.info("Adding Violations to DB", count=len(violations))
    result = DataQualitySchemaViolationRepo(db).bulk_insert(violations)
    log.info("Successfully added violations to DB", count=len(result))
    return result
