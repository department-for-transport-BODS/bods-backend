"""
File Attributes Lambda
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationTXCFileAttributes
from common_layer.database.repos import (
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.download import download_and_parse_txc
from common_layer.s3.utils import get_filename_from_object_key
from common_layer.txc.models import TXCData
from common_layer.txc.parser.parser_txc import TXCParserConfig
from structlog.stdlib import get_logger

from tests.timetables_etl.pti.test_pti_validation import s3_file

from .models import FileAttributesInputData
from .process_txc import make_txc_file_attributes

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


def replace_filename_with_object_key(
    file_attributes: OrganisationTXCFileAttributes, s3_file_key: str
) -> OrganisationTXCFileAttributes:
    """
    The current BODs uses the file name of the XML on disk
    However ideally it would be the filename from the Metadata
    In the future we could have a check for this to ensure both are the same
    However there are files with different FileName metadata to the disk name
    So we this function matches the original bods implementation
    """

    try:
        filename = get_filename_from_object_key(s3_file_key)
        if filename:
            file_attributes.filename = filename
            log.info(
                "File Name Updated",
                original_filename=file_attributes.filename,
                new_filename=filename,
                s3_key=s3_file_key,
            )
        else:
            log.warning(
                "Unable To Extract Filename From S3 Key",
                s3_key=s3_file_key,
                current_filename=file_attributes.filename,
            )
    except AttributeError:
        log.error(
            "Error Processing Filename",
            s3_key=s3_file_key,
            current_filename=file_attributes.filename,
            exc_info=True,
        )

    return file_attributes


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
    file_attributes_data = replace_filename_with_object_key(
        file_attributes_data, input_data.s3_file_key
    )
    log.debug(
        "TXC File Attributes Processed", file_attributes_data=file_attributes_data
    )
    return OrganisationTXCFileAttributesRepo(db).insert(file_attributes_data)


@file_processing_result_to_db(StepName.TXC_ATTRIBUTE_EXTRACTION)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, int]:
    """
    Main lambda handler
    """
    input_data = FileAttributesInputData(**event)
    txc_data = download_and_parse_txc(
        input_data.s3_bucket_name, input_data.s3_file_key, PARSER_CONFIG
    )
    db = SqlDB()
    inserted_data = process_file_attributes(input_data, txc_data, db)
    log.info("TXC File Attributes added to database", inserted_data=inserted_data)
    return {"id": inserted_data.id}
