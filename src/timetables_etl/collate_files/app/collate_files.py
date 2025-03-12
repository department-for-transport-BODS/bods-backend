"""
Lambda: CollateFiles
Process the results
"""

from typing import Any, Counter

from aws_lambda_powertools.utilities.typing import LambdaContext
from collate_files.app.models import S3FileReference
from common_layer.aws.step import get_map_processing_results
from common_layer.database import SqlDB
from common_layer.database.models import OrganisationTXCFileAttributes
from common_layer.database.repos import OrganisationTXCFileAttributesRepo
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .models import CollateFilesInputData
from .txc_filtering import (
    create_etl_inputs_from_map_results,
    filter_txc_files_by_service_code,
)

log = get_logger()


def get_file_attributes(
    db: SqlDB, revision_id: int
) -> list[OrganisationTXCFileAttributes]:
    """
    Return the list of file attributes for a revision_id
    """

    file_attributes = OrganisationTXCFileAttributesRepo(db).get_by_revision_id(
        revision_id
    )
    log.info(
        "File Attributes for revision ID returned",
        file_attributes_ids=[file.id for file in file_attributes],
        revision_id=revision_id,
    )
    return file_attributes


def count_and_log_file_status(
    map_inputs: list[S3FileReference],
) -> tuple[int, int]:
    """
    Count superceded and active files in map inputs and log the results.
    """
    counts = Counter(input_file.superceded_file for input_file in map_inputs)
    superceded_count = counts.get(True, 0)
    active_count = counts.get(False, 0)

    log.info(
        "ETL inputs created from map results",
        superceded_files=superceded_count,
        active_files=active_count,
        total_files=len(map_inputs),
    )

    return superceded_count, active_count


def collate_files(
    input_data: CollateFilesInputData, db: SqlDB, s3: S3
) -> list[S3FileReference]:
    """
    Collate the files
    """
    file_attributes = get_file_attributes(db, input_data.revision_id)
    map_results = get_map_processing_results(
        s3, input_data.map_run_arn, input_data.map_run_prefix
    )
    filtered_files = filter_txc_files_by_service_code(file_attributes)

    map_inputs = create_etl_inputs_from_map_results(
        all_files=file_attributes,
        filtered_files=filtered_files,
        map_results=map_results,
        revision_id=input_data.revision_id,
    )
    count_and_log_file_status(map_inputs)

    return map_inputs


def generate_response(map_inputs: list[S3FileReference]) -> dict[str, str | int]:
    """
    Generate Lambda Response with Stats
    """
    superseded, active = count_and_log_file_status(map_inputs)

    if superseded == 0:
        message = "All TXC Files that completed TXC File Attributes Step are active"
    else:
        message = (
            "Duplicate Service Code TXC Files found. "
            "Filtering rules applied and superseded files will have special processing"
        )

    return {
        "status_code": 200,
        "message": message,
        "active_files": active,
        "superceded": superseded,
    }


@file_processing_result_to_db(step_name=StepName.FILE_COLLATION)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Lambda Handler for CollateFiles
    """
    input_data = CollateFilesInputData(**event)
    db = SqlDB()
    s3 = S3(input_data.s3_bucket_name)
    map_inputs = collate_files(input_data, db, s3)

    return generate_response(map_inputs)
