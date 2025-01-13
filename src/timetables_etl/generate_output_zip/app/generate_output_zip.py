"""
GenerateOutputZip Lambda
Runs after the End of the FileProcessingMap to Zip the successful files
"""

from datetime import UTC, datetime
from io import BytesIO

from common_layer.database.client import SqlDB
from common_layer.json_logging import configure_logging
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
from .zip_processing import generate_zip_file

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


def upload_zip_to_s3(s3_client: S3, zip_buffer: BytesIO, output_key: str) -> None:
    """
    Upload a zip file to S3
    """
    log.info("Uploading Generated Zip to S3", output_key=output_key)
    s3_client.upload_fileobj_streaming(
        fileobj=zip_buffer, file_path=output_key, content_type="application/zip"
    )


def zip_and_upload_successful_files(
    s3_client: S3, successful_files: list[MapExecutionSucceeded], output_key: str
) -> ProcessingResult:
    """
    Create a zip file containing all successfully processed files and upload it to S3
    """
    zip_buffer, zip_count, failed_count = generate_zip_file(s3_client, successful_files)
    file_hash = get_bytes_hash(zip_buffer)
    upload_zip_to_s3(s3_client, zip_buffer, output_key)
    return ProcessingResult(
        successful_files=zip_count,
        failed_files=failed_count,
        zip_location=output_key,
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


def process_map_results(input_data: GenerateOutputZipInputData) -> ProcessingResult:
    """
    Process the map results and create a zip file of successful files


    """
    s3_client = S3(input_data.destination_bucket)

    map_run_id = extract_map_run_id(input_data.map_run_arn)
    log.info("Processing map results", map_run_id=map_run_id)

    map_results = load_map_results(s3_client, input_data.output_prefix, map_run_id)
    log_failed_files(map_results.failed)

    # TEMPORARY: The ETL is supposed to overwrite the original file
    # However this makes it hard to test so output to a different file for now
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    zip_key = f"{input_data.original_object_key}etl_output_{timestamp}.zip"
    processing_result = zip_and_upload_successful_files(
        s3_client, map_results.succeeded, zip_key
    )
    db = SqlDB()
    update_revision_hash(
        db, input_data.dataset_revision_id, processing_result.file_hash
    )
    return processing_result


def lambda_handler(event, _context):
    """
    Lambda handler for generating zip file from map state results
    """
    configure_logging()
    input_data = GenerateOutputZipInputData(**event)
    result = process_map_results(input_data)

    log.info(
        "Completed zip generation",
        successful_files=result.successful_files,
        failed_files=result.failed_files,
        zip_location=result.zip_location,
    )

    return {
        "statusCode": 200,
        "body": {
            "message": "Successfully generated zip file",
            "successful_files": result.successful_files,
            "failed_files": result.failed_files,
            "zip_location": result.zip_location,
        },
    }
