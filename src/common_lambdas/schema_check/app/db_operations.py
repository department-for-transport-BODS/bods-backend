"""
Database Operations for Schema Check
"""

from datetime import UTC, datetime

from common_layer.database.models.model_data_quality import DataQualitySchemaViolation
from common_layer.database.repos.repo_data_quality import (
    add_schema_violations_to_db as add_violations_to_db,
    create_violation_from_parse_error,
)
from lxml.etree import _LogEntry  # type: ignore

__all__ = [
    "add_violations_to_db",
    "create_violation_from_parse_error",
    "create_violation_from_error",
]


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
