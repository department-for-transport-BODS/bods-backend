"""
Database operations for file validation.
"""

from datetime import UTC, datetime

from common_layer.database.client import SqlDB
from common_layer.database.models.model_data_quality import DataQualitySchemaViolation
from common_layer.database.repos.repo_data_quality import DataQualitySchemaViolationRepo


def create_violation_from_parse_error(
    exc: Exception, revision_id: int, filename: str
) -> DataQualitySchemaViolation:
    """Create a schema violation from an XML parse error."""
    line_number = getattr(exc, "lineno", None)
    message = getattr(exc, "msg", None)

    return DataQualitySchemaViolation(
        filename=filename,
        line=line_number if isinstance(line_number, int) else 0,
        details=message if isinstance(message, str) else str(exc),
        created=datetime.now(UTC),
        revision_id=revision_id,
    )


def add_violations_to_db(
    db: SqlDB, violations: list[DataQualitySchemaViolation]
) -> list[DataQualitySchemaViolation]:
    """Insert file validation violations into the database."""
    if not violations:
        return []
    return DataQualitySchemaViolationRepo(db).bulk_insert(violations)
