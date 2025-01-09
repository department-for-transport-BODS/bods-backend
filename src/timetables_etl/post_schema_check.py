"""
PostSchemaCheck Lambda
"""

import re
from datetime import UTC, datetime
from typing import Callable

from aws_lambda_powertools import Tracer
from common_layer.database.client import SqlDB
from common_layer.database.models.model_data_quality import (
    DataQualityPostSchemaViolation,
)
from common_layer.database.repos.repo_data_quality import (
    DataQualityPostSchemaViolationRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.download import download_and_parse_txc
from common_layer.json_logging import configure_logging
from common_layer.txc.models.txc_data import TXCData
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

tracer = Tracer()
log = get_logger()


class PostSchemaCheckInputData(BaseModel):
    """
    Input data for the Post Schema Check
    """

    class Config:
        """
        Allow us to map Bucket / Object Key
        """

        populate_by_name = True

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")


class ValidationResult(BaseModel):
    """
    Result of a validation check with details
    """

    is_valid: bool
    error_code: str | None = None
    message: str | None = None


ValidatorFn = Callable[[TXCData], ValidationResult]


def check_filename_for_filepath_pii(txc_data: TXCData) -> ValidationResult:
    """
    Check if a TransXChange document's filename contains potential PII through filepath information.

    Examines the FileName attribute of a TransXChange document for path separators:
    - Backslashes which indicate Windows-style file paths
    - Forward slashes which indicate Unix (Mac / Linux) file paths
    Both may contain usernames or sensitive path information
    """
    if txc_data.Metadata is None:
        return ValidationResult(is_valid=True)

    windows_paths = re.findall("\\\\", txc_data.Metadata.FileName)
    unix_paths = re.findall("/", txc_data.Metadata.FileName)

    if len(windows_paths) > 0 or len(unix_paths) > 0:
        log.warning("Found potential file path in TransXChange FileName Attribute")
        return ValidationResult(
            is_valid=False,
            error_code="PII_ERROR",
            message="Filename contains potential filepath PII",
        )
    return ValidationResult(is_valid=True)


def run_post_schema_validations(txc_data: TXCData) -> list[ValidationResult]:
    """
    Run all validators and return their results
    """
    validators: list[ValidatorFn] = [
        check_filename_for_filepath_pii,
    ]

    results: list[ValidationResult] = []

    for validator in validators:
        result = validator(txc_data)
        if not result.is_valid:
            log.info(
                "Validation failed",
                validator=validator.__name__,
                error_code=result.error_code,
                message=result.message,
            )
        results.append(result)

    return results


def process_txc_data_check(txc_data: TXCData) -> list[str]:
    """
    Process validations that are separate from XML XSD Schema and PTI
    """
    results = run_post_schema_validations(txc_data)

    violations = [
        result.error_code
        for result in results
        if not result.is_valid and result.error_code is not None
    ]

    if not violations:
        log.info("All post-schema validations passed")

    return violations


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


def process_post_schema_check(
    db: SqlDB, input_data: PostSchemaCheckInputData, txc_data: TXCData
):
    """
    Process the schema check
    """
    violation_strs = process_txc_data_check(txc_data)
    db_violations = create_schema_violations_objects(
        input_data.revision_id, input_data.s3_file_key, violation_strs
    )
    add_violations_to_db(db, db_violations)


@file_processing_result_to_db(step_name=StepName.TIMETABLE_POST_SCHEMA_CHECK)
def lambda_handler(event, _context):
    """
    PostSchemaCheck Currently only checks for file paths in FileName
    """
    configure_logging()
    input_data = PostSchemaCheckInputData(**event)
    db = SqlDB()
    txc_data = download_and_parse_txc(input_data.s3_bucket_name, input_data.s3_file_key)
    process_post_schema_check(db, input_data, txc_data)

    return {"statusCode": 200, "body": "Completed Post Schema Check"}
