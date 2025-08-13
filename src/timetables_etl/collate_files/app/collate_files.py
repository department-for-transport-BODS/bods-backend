"""
Lambda: CollateFiles
Process the results
"""

from io import BytesIO
from typing import Any, Counter

import common_layer.aws.datadog.tracing  # type: ignore # pylint: disable=unused-import
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.aws.step import get_map_processing_results, get_map_run_base_path
from common_layer.database import SqlDB
from common_layer.database.models import OrganisationTXCFileAttributes
from common_layer.database.repos import OrganisationTXCFileAttributesRepo
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from common_layer.utils import send_failure_email
from pydantic import RootModel
from structlog.stdlib import get_logger

from .models import CollateFilesInputData, ETLMapInputData
from .txc_filtering import (
    create_etl_inputs_from_map_results,
    deduplicate_file_attributes_by_filename,
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
    file_attributes = deduplicate_file_attributes_by_filename(file_attributes)
    return file_attributes


def count_and_log_file_status(
    map_inputs: list[ETLMapInputData],
) -> tuple[int, int]:
    """
    Count superceded and active files in map inputs and log the results.
    """
    counts = Counter(input_file.superseded_timetable for input_file in map_inputs)
    superceded_count = counts.get(True, 0)
    active_count = counts.get(False, 0)

    log.info(
        "ETL inputs created from map results",
        superceded_files=superceded_count,
        active_files=active_count,
        total_files=len(map_inputs),
    )

    return superceded_count, active_count


def upload_map_input_to_s3(
    s3: S3, output_prefix: str, map_inputs: list[ETLMapInputData]
) -> str:
    """
    Upload the map input to S3
    """
    output_key = f"{output_prefix}collated_files.json"
    root_model = RootModel[list[ETLMapInputData]](map_inputs)
    map_inputs_json = root_model.model_dump_json(indent=2, by_alias=True)
    try:
        fileobj = BytesIO(map_inputs_json.encode("utf-8"))

        s3.upload_fileobj_streaming(
            fileobj=fileobj, file_path=output_key, content_type="application/json"
        )

        log.info(
            "Successfully uploaded map inputs to S3",
            output_key=output_key,
            file_count=len(map_inputs),
        )
        return output_key
    except Exception:
        log.error(
            "Failed to upload map inputs to S3", output_key=output_key, exc_info=True
        )
        raise


def collate_files(
    input_data: CollateFilesInputData, db: SqlDB, s3: S3
) -> tuple[list[ETLMapInputData], str]:
    """
    - Get the File Attributes for the Revision ID
    - Get the Map Processing Results from S3
    - Process using the BODs filtering logic by Service ID / Start Date
    - Generate the PTI+ETL Map Input Data
    - Upload to S3 and return Object Key
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
    )

    count_and_log_file_status(map_inputs)
    log.info("Map Result", map_results=map_results)
    if map_results.failed:
        log.info("Sending the error email", revision_id=input_data.revision_id)
        send_failure_email(db, input_data.revision_id)

    output_prefix = get_map_run_base_path(
        input_data.map_run_arn, input_data.map_run_prefix
    )
    object_key = upload_map_input_to_s3(s3, output_prefix, map_inputs)
    return map_inputs, object_key


def generate_response(
    map_inputs: list[ETLMapInputData], s3_object_key: str
) -> dict[str, str | int | dict[str, int]]:
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
        "statusCode": 200,
        "message": message,
        "stats": {
            "activeFiles": active,
            "supercededFiles": superseded,
        },
        "EtlFileListJsonS3ObjectKey": s3_object_key,
    }


@file_processing_result_to_db(step_name=StepName.FILE_COLLATION)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Lambda Handler for CollateFiles
    """
    input_data = CollateFilesInputData(**event)
    db = SqlDB()
    s3 = S3(input_data.s3_bucket_name)
    map_inputs, s3_object_key = collate_files(input_data, db, s3)

    return generate_response(map_inputs, s3_object_key)
