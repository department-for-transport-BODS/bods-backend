"""
Functions to output the found Violations to DB
"""

from datetime import UTC, datetime

from common_layer.database.client import SqlDB
from common_layer.database.models import DataQualityPostSchemaViolation
from common_layer.database.repos import DataQualityPostSchemaViolationRepo
from structlog.stdlib import get_logger

from .models import ValidationResult

log = get_logger()


def create_schema_violations_objects(
    revision_id: int,
    filename: str,
    violations: list[ValidationResult],
) -> list[DataQualityPostSchemaViolation]:
    """
    Construct data to put into DB
    """
    db_violations: list[DataQualityPostSchemaViolation] = []
    for violation in violations:
        if violation.error_code is not None:
            db_violations.append(
                DataQualityPostSchemaViolation(
                    filename=filename,
                    details=violation.error_code,
                    additional_details=(
                        violation.additional_details.model_dump()
                        if violation.additional_details
                        else {}
                    ),
                    created=datetime.now(UTC),
                    revision_id=revision_id,
                )
            )
        else:
            log.error(
                "Violation Error Code Missing, skipping adding to DB",
                violation=violation,
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
