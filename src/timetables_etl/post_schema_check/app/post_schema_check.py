"""
PostSchemaCheck Lambda
"""

from aws_lambda_powertools import Tracer
from common_layer.database.client import SqlDB
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.download import download_and_parse_txc
from common_layer.txc.models.txc_data import TXCData
from common_layer.txc.parser.parser_txc import TXCParserConfig
from structlog.stdlib import get_logger

from .db_output import add_violations_to_db, create_schema_violations_objects
from .models import PostSchemaCheckInputData
from .post_schema_validation import run_post_schema_validations

tracer = Tracer()
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


@tracer.capture_lambda_handler
@file_processing_result_to_db(step_name=StepName.TIMETABLE_POST_SCHEMA_CHECK)
def lambda_handler(event, _context):
    """
    PostSchemaCheck Currently only checks for file paths in FileName
    """
    input_data = PostSchemaCheckInputData(**event)
    db = SqlDB()
    txc_data = download_and_parse_txc(
        input_data.s3_bucket_name, input_data.s3_file_key, PARSER_CONFIG
    )
    process_post_schema_check(db, input_data, txc_data)

    return {"statusCode": 200, "body": "Completed Post Schema Check"}
