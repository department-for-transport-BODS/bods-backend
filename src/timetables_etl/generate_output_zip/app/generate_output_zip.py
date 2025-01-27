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
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from common_layer.txc.parser.hashing import get_bytes_hash
from structlog.stdlib import get_logger

from .db_operations import update_revision_hash
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


def construct_output_path(original_path: str, is_test_mode: bool = True) -> str:
    """
    Construct the output file path based on the original path.
    In test mode, appends a timestamp to avoid overwriting.
    In production mode, will overwrite the original file.
    """
    path = Path(original_path.rstrip("/"))

    if not is_test_mode:
        # In production, we'll overwrite the original file
        return str(path.with_suffix(""))

    # In test mode, create a new file with timestamp
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    stem = path.stem  # Get filename without extension

    # Handle cases where the original path might have multiple extensions
    # e.g. "file.xml.zip" -> "file"
    while "." in stem:
        stem = Path(stem).stem

    return str(path.with_name(f"{stem}_etl_output_{timestamp}"))


def process_map_results(input_data: GenerateOutputZipInputData) -> ProcessingResult:
    """
    Process the map results and create an output file of successful files


    """
    s3_client = S3(input_data.destination_bucket)

    map_run_id = extract_map_run_id(input_data.map_run_arn)
    log.info("Processing map results", map_run_id=map_run_id)

    map_results = load_map_results(s3_client, input_data.output_prefix, map_run_id)
    log_failed_files(map_results.failed)

    # TEMPORARY: The ETL is supposed to overwrite the original file
    # However this makes it hard to test so output to a different file for now
    output_key_base = construct_output_path(input_data.original_object_key, True)
    processing_result = process_and_upload_successful_files(
        s3_client, map_results.succeeded, output_key_base
    )
    db = SqlDB()
    update_revision_hash(
        db, input_data.dataset_revision_id, processing_result.file_hash
    )
    return processing_result


@file_processing_result_to_db(StepName.GENERATE_OUTPUT_ZIP)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for generating zip file from map state results
    """
    input_data = GenerateOutputZipInputData(**event)
    result = process_map_results(input_data)

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
