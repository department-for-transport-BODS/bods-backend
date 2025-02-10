"""
PostSchemaCheck Lambda
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.models import DataQualityPostSchemaViolation
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.download import download_and_parse_txc
from common_layer.s3.utils import get_filename_from_object_key
from common_layer.txc.models.txc_data import TXCData
from common_layer.txc.parser.parser_txc import TXCParserConfig
from structlog.stdlib import get_logger

from .db_output import add_violations_to_db, create_schema_violations_objects
from .models import PostSchemaCheckInputData, ValidationResult
from .post_schema_validation import run_post_schema_validations

log = get_logger()

PARSER_CONFIG = TXCParserConfig(
    metadata=True,
    serviced_organisations=False,
    stop_points=False,
    routes=False,
    route_sections=False,
    journey_pattern_sections=False,
    services=False,
    operators=False,
    vehicle_journeys=False,
    track_data=False,
    file_hash=False,
)


def process_txc_data_check(txc_data: TXCData, db: SqlDB) -> list[ValidationResult]:
    """
    Process validations that are separate from XML XSD Schema and PTI
    """
    results = run_post_schema_validations(txc_data, db)

    violations = [
        result
        for result in results
        if not result.is_valid and result.error_code is not None
    ]

    if not violations:
        log.info("All post-schema validations passed")
    else:
        log.info("Post-schema Violations found", count=len(violations))
    return violations


def process_post_schema_check(
    db: SqlDB, input_data: PostSchemaCheckInputData, txc_data: TXCData
) -> tuple[list[ValidationResult], list[DataQualityPostSchemaViolation]]:
    """
    Process the schema check
    """
    violations = process_txc_data_check(txc_data, db)
    filename = get_filename_from_object_key(input_data.s3_file_key)
    if not filename:
        raise ValueError(
            f"Unable to parse filename from input_data.s3_file_key: {input_data.s3_file_key}"
        )
    db_violations = create_schema_violations_objects(
        input_data.revision_id, filename, violations
    )
    add_violations_to_db(db, db_violations)
    log.info(
        "Violations Processed",
        violations_count=len(violations),
        added_to_db_count=len(db_violations),
    )
    return violations, db_violations


class PostSchemaViolationsFound(Exception):
    """
    Exception raised when schema violation is found
    """


@file_processing_result_to_db(step_name=StepName.TIMETABLE_POST_SCHEMA_CHECK)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    PostSchemaCheck Currently only checks for file paths in FileName
    """
    input_data = PostSchemaCheckInputData(**event)
    db = SqlDB()
    txc_data = download_and_parse_txc(
        input_data.s3_bucket_name, input_data.s3_file_key, PARSER_CONFIG
    )
    violations, _db_violations = process_post_schema_check(db, input_data, txc_data)

    if violations:
        raise PostSchemaViolationsFound(
            f"Found {len(violations)} Post Schema Violations"
        )

    return {"statusCode": 200, "body": "Completed Post Schema Check"}
