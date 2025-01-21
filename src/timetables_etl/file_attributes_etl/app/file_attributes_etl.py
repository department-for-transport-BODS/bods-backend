"""
File Attributes Lambda
"""

from aws_lambda_powertools import Tracer
from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationTXCFileAttributes
from common_layer.database.repos import (
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.download import download_and_parse_txc
from common_layer.json_logging import configure_logging
from common_layer.txc.models import TXCData
from common_layer.txc.parser.parser_txc import TXCParserConfig
from structlog.stdlib import get_logger

from .models import FileAttributesInputData
from .process_txc import make_txc_file_attributes

tracer = Tracer()
log = get_logger()

PARSER_CONFIG = TXCParserConfig(
    metadata=True,
    services=True,
    operators=True,
    file_hash=True,
    serviced_organisations=False,
    stop_points=False,
    route_sections=False,
    routes=False,
    journey_pattern_sections=False,
    vehicle_journeys=False,
    track_data=False,
)


def process_file_attributes(
    input_data: FileAttributesInputData, txc_data: TXCData, db: SqlDB
) -> OrganisationTXCFileAttributes:
    """
    Process the file attributes
    """
    revision = OrganisationDatasetRevisionRepo(db).get_by_id(input_data.revision_id)
    if revision is None:
        log.error("Could not Find Revision by ID", revision_id=input_data.revision_id)
        raise ValueError("Revision ID Not Found")

    file_attributes_data = make_txc_file_attributes(txc_data, revision)
    log.debug(
        "TXC File Attributes Processed", file_attributes_data=file_attributes_data
    )
    return OrganisationTXCFileAttributesRepo(db).insert(file_attributes_data)


@tracer.capture_lambda_handler
@file_processing_result_to_db(StepName.TXC_ATTRIBUTE_EXTRACTION)
def lambda_handler(event, _context) -> dict[str, int]:
    """
    Main lambda handler
    """
    configure_logging()
    input_data = FileAttributesInputData(**event)
    txc_data = download_and_parse_txc(
        input_data.s3_bucket_name, input_data.s3_file_key, PARSER_CONFIG
    )
    db = SqlDB()
    inserted_data = process_file_attributes(input_data, txc_data, db)
    log.info("TXC File Attributes added to database", inserted_data=inserted_data)
    return {"id": inserted_data.id}
