"""
Functions to output the found Violations to DB
"""

from datetime import UTC, datetime

from common_layer.database.client import SqlDB
from common_layer.database.models import DataQualityPostSchemaViolation
from common_layer.database.repos import DataQualityPostSchemaViolationRepo
from structlog.stdlib import get_logger

log = get_logger()


def create_schema_violations_objects(
    revision_id: int,
    filename: str,
    violations: list[str],
) -> list[DataQualityPostSchemaViolation]:
    """
    Construct data to put into DB
    """
    db_violations: list[DataQualityPostSchemaViolation] = []
    for violation in violations:
        db_violations.append(
            DataQualityPostSchemaViolation(
                filename=filename,
                details=violation,
                created=datetime.now(UTC),
                revision_id=revision_id,
            )
        )
    return db_violations


def add_violations_to_db(
    db: SqlDB, violations: list[DataQualityPostSchemaViolation]
) -> list[DataQualityPostSchemaViolation]:
    """
    Add post schema violations found to DB
    """
    if len(violations) == 0:
        log.info("No Violations found. Skipping Database Insert of Violations")
        return []
    log.info("Adding Violations to DB", count=len(violations))
    result = DataQualityPostSchemaViolationRepo(db).bulk_insert(violations)
    log.info(
        "Successfully added violations to DB",
        count=len(result),
        ids=[item.id for item in result],
    )
    return result
