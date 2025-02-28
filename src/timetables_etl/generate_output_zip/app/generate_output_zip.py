"""
GenerateOutputZip Lambda
Runs after the End of the FileProcessingMap to Zip the successful files
"""

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_etl_task import ETLTaskResultRepo
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from common_layer.xml.utils.hashing import get_bytes_hash
from structlog.stdlib import get_logger

from .db_operations import (
    publish_revision,
    update_live_revision,
    update_revision_hash,
    update_task_and_revision_status,
)
from .map_results import load_map_results
from .models import (
    GenerateOutputZipInputData,
    MapExecutionFailed,
    MapExecutionSucceeded,
    ProcessingResult,
)
from .output_processing import process_files

log = get_logger()


def extract_map_run_id(map_run_arn: str) -> str:
    """
    Extract the Map Run Id from the ARN
    Example ARN: arn:aws:states:region:account:mapRun:state-machine-name/execution-id:map-run-id
    Returns: map-run-id
    """
    try:
        return map_run_arn.split("/")[-1].split(":")[-1]
    except Exception as exc:
        log.error(
            "Failed to extract Map Run Id from ARN",
            map_run_arn=map_run_arn,
            exc_info=True,
        )
        raise ValueError(f"Invalid Map Run ARN format: {map_run_arn}") from exc


def upload_output_to_s3(
    s3_client: S3, file_buffer: BytesIO, output_key: str, content_type: str
) -> None:
    """
    Upload a file to S3
    """
    log.info("Uploading Generated file to S3", output_key=output_key)
    s3_client.upload_fileobj_streaming(
        fileobj=file_buffer, file_path=output_key, content_type=content_type
    )


def process_and_upload_successful_files(
    s3_client: S3, successful_files: list[MapExecutionSucceeded], output_key_base: str
) -> ProcessingResult:
    """
    Process files and upload to S3 - either as single XML or ZIP file depending on count
    """
    file_buffer, success_count, failed_count, extension = process_files(
        s3_client, successful_files
    )

    # Update the output key with the correct extension
    output_key = f"{output_key_base}{extension}"

    content_type = "application/xml" if extension == ".xml" else "application/zip"
    file_hash = get_bytes_hash(file_buffer)

    upload_output_to_s3(s3_client, file_buffer, output_key, content_type)

    return ProcessingResult(
        successful_files=success_count,
        failed_files=failed_count,
        output_location=output_key,
        file_hash=file_hash,
    )


def log_failed_files(failed_files: list[MapExecutionFailed]):
    """
    Log the Failed Files
    """
    if failed_files:
        log.error(
            "Failed Files in Map",
            failed_files=[f.Name for f in failed_files],
        )


def construct_output_path(
    original_path: str, overwrite_input_dataset: bool = True
) -> str:
    """
    Construct the output file path based on the original path.
    When testing, appends a timestamp to avoid overwriting.
    Normally we will overwrite the original file.
    """
    path = Path(original_path.rstrip("/"))

    if overwrite_input_dataset:
        output_path = str(path.with_suffix(""))
        log.info("Overwriting original file in S3", output_path=output_path)
        return output_path

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    stem = path.stem  # Get filename without extension

    # Handle cases where the original path might have multiple extensions
    # e.g. "file.xml.zip" -> "file"
    while "." in stem:
        stem = Path(stem).stem
    output_path = str(path.with_name(f"{stem}_etl_output_{timestamp}"))
    log.info(
        "Generating different output path to prevent overwritin input data",
        output_path=output_path,
    )
    return output_path


def process_map_results(
    input_data: GenerateOutputZipInputData, db: SqlDB
) -> ProcessingResult:
    """
    Process the map results, create an output file of successful files
    and update task/revision statuses
    """
    s3_client = S3(input_data.destination_bucket)

    map_run_id = extract_map_run_id(input_data.map_run_arn)
    log.info("Processing map results", map_run_id=map_run_id)

    map_results = load_map_results(s3_client, input_data.output_prefix, map_run_id)
    log_failed_files(map_results.failed)

    output_key_base = construct_output_path(
        input_data.original_object_key, input_data.overwrite_input_dataset
    )
    processing_result = process_and_upload_successful_files(
        s3_client, map_results.succeeded, output_key_base
    )
    update_revision_hash(
        db, input_data.dataset_revision_id, processing_result.file_hash
    )

    revision = update_task_and_revision_status(
        db,
        map_results,
        processing_result,
        input_data.dataset_etl_task_result_id,
        input_data.dataset_revision_id,
    )

    if input_data.publish_dataset_revision:
        publish_revision(db, revision)
        update_live_revision(db, revision)

    return processing_result


@file_processing_result_to_db(StepName.GENERATE_OUTPUT_ZIP)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for generating zip file from map state results
    """
    input_data = GenerateOutputZipInputData(**event)
    db = SqlDB()
    ETLTaskResultRepo(db).update_progress(input_data.dataset_etl_task_result_id, 90)
    result = process_map_results(input_data, db)
    ETLTaskResultRepo(db).update_progress(input_data.dataset_etl_task_result_id, 100)
    log.info(
        "Completed output generation",
        successful_files=result.successful_files,
        failed_files=result.failed_files,
        zip_location=result.output_location,
    )

    return {
        "statusCode": 200,
        "body": {
            "message": "Successfully generated output file",
            "successful_files": result.successful_files,
            "failed_files": result.failed_files,
            "output_location": result.output_location,
        },
    }
