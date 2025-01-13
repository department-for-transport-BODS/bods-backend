"""
GenerateOutputZip Lambda
Runs after the End of the FileProcessingMap to Zip the successful files
"""

import zipfile
from datetime import UTC, datetime
from io import BytesIO

from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .map_results import load_map_results
from .models import (
    GenerateOutputZipInputData,
    MapExecutionFailed,
    MapExecutionSucceeded,
    ProcessingResult,
)

log = get_logger()


def extract_map_run_id(map_run_arn: str) -> str:
    """
    Extract the Map Run Id from the ARN
    Example ARN: arn:aws:states:region:account:mapRun:state-machine-name/map-run-id
    Returns: map-run-id
    """
    try:
        return map_run_arn.split("/")[-1]
    except Exception as exc:
        log.error(
            "Failed to extract Map Run Id from ARN",
            map_run_arn=map_run_arn,
            exc_info=True,
        )
        raise ValueError(f"Invalid Map Run ARN format: {map_run_arn}") from exc


def create_zip_from_successful_files(
    s3_client: S3, successful_files: list[MapExecutionSucceeded], output_key: str
) -> ProcessingResult:
    """
    Create a zip file containing all successfully processed files with optimized XML compression
    """
    zip_buffer = BytesIO()
    zip_count = 0
    failed_count = 0

    with zipfile.ZipFile(
        zip_buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zip_file:
        for file in successful_files:
            if file.parsed_input and file.parsed_input.Key:
                try:
                    with s3_client.get_object(file.parsed_input.Key) as stream:
                        filename = file.parsed_input.Key.split("/")[-1]
                        zip_file.writestr(filename, stream.read())
                        zip_count += 1

                        log.info(
                            "Added File to Zip",
                            filename=filename,
                            compression_type="deflated",
                            compression_level=9,
                        )
                except (
                    # We want to always skip error files
                    Exception  # pylint: disable=broad-exception-caught
                ):
                    log.error(
                        "Failed too Add file to Zip",
                        filename=file.parsed_input.Key,
                        exc_info=True,
                    )
                    failed_count += 1
            else:
                log.warning(
                    "Sucessful File Missing Parsed Input Data",
                    input_data=file.Input,
                    exc_info=True,
                )

    zip_buffer.seek(0)

    s3_client.put_object(
        output_key,
        zip_buffer.getvalue(),
    )

    return ProcessingResult(
        successful_files=zip_count, failed_files=failed_count, zip_location=output_key
    )


def log_failed_files(failed_files: list[MapExecutionFailed]):
    """
    Log the Failed Files
    """
    log.error(
        "Failed Files in Map",
        failed_files=[f.Name for f in failed_files],
    )


def process_map_results(input_data: GenerateOutputZipInputData) -> ProcessingResult:
    """
    Process the map results and create a zip file of successful files
    """
    s3_client = S3(input_data.destination_bucket)

    # Extract Map Run Id from ARN
    map_run_id = extract_map_run_id(input_data.map_run_arn)
    log.info("Processing map results", map_run_id=map_run_id)

    map_results = load_map_results(s3_client, input_data.output_prefix, map_run_id)
    log_failed_files(map_results.failed)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    zip_key = f"{input_data.output_prefix}/processed_files_{timestamp}.zip"

    return create_zip_from_successful_files(s3_client, map_results.succeeded, zip_key)


def lambda_handler(event, _context):
    """
    Lambda handler for generating zip file from map state results
    """
    configure_logging()
    input_data = GenerateOutputZipInputData(**event)
    result = process_map_results(input_data)

    log.info(
        "Completed zip generation",
        successful_files=result["successful_files"],
        failed_files=result["failed_files"],
        zip_location=result["zip_location"],
    )

    return {
        "statusCode": 200,
        "body": {
            "message": "Successfully generated zip file",
            "successful_files": result["successful_files"],
            "failed_files": result["failed_files"],
            "zip_location": result["zip_location"],
        },
    }
