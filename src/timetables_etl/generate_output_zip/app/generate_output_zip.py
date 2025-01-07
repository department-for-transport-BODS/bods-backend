"""
GenerateOutputZip Lambda
Runs after the End of the FileProcessingMap to Zip the successful files
"""

import json
import zipfile
from datetime import UTC, datetime
from io import BytesIO

from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .models import GenerateOutputZipInputData, MapResults, ProcessingResult, ResultFile

log = get_logger()


def extract_map_run_id(map_run_arn: str) -> str:
    """
    Extract the Map Run Id from the ARN
    Example ARN: arn:aws:states:region:account:mapRun:state-machine-name/map-run-id
    Returns: map-run-id
    """
    try:
        return map_run_arn.split("/")[-1]
    except Exception:
        log.error(
            "Failed to extract Map Run Id from ARN",
            map_run_arn=map_run_arn,
            exc_info=True,
        )
        raise ValueError(f"Invalid Map Run ARN format: {map_run_arn}")


def read_manifest(s3_client: S3, output_prefix: str, map_run_id: str) -> MapResults:
    """
    Read and parse the manifest.json file from the map results
    """
    manifest_key = f"{output_prefix}/tt-etl-map-results/{map_run_id}/manifest.json"

    log.info(
        "Reading manifest file",
        bucket=s3_client.bucket_name,
        key=manifest_key,
        map_run_id=map_run_id,
    )

    try:
        manifest_data = s3_client.get_object(manifest_key)
        return MapResults.parse_raw(manifest_data.read())
    except Exception as e:
        log.error(
            "Failed to read manifest file",
            bucket=s3_client.bucket_name,
            key=manifest_key,
            map_run_id=map_run_id,
            error=str(e),
        )
        raise


def create_zip_from_successful_files(
    s3_client: S3, successful_files: list[ResultFile], output_key: str
) -> ProcessingResult:
    """
    Create a zip file containing all successfully processed files
    """
    zip_buffer = BytesIO()
    zip_count = 0
    failed_count = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in successful_files:
            try:
                file_content = s3_client.get_object(file.Key)

                # Extract just the filename from the full path
                filename = file.Key.split("/")[-1]
                zip_file.writestr(filename, file_content.read())
                zip_count += 1

                log.info("Added file to zip", filename=filename)
            except Exception as e:
                log.error("Failed to add file to zip", filename=file.Key, error=str(e))
                failed_count += 1

    # Upload the zip file to S3
    zip_buffer.seek(0)
    s3_client.put_object(output_key, zip_buffer.getvalue())

    return ProcessingResult(
        successful_files=zip_count, failed_files=failed_count, zip_location=output_key
    )


def process_map_results(input_data: GenerateOutputZipInputData) -> ProcessingResult:
    """
    Process the map results and create a zip file of successful files
    """
    s3_client = S3(input_data.destination_bucket)

    # Extract Map Run Id from ARN
    map_run_id = extract_map_run_id(input_data.map_run_arn)
    log.info("Processing map results", map_run_id=map_run_id)

    # Read the manifest file using the correct path with Map Run Id
    manifest = read_manifest(s3_client, input_data.output_prefix, map_run_id)

    # Log any failed files
    if manifest.ResultFiles.FAILED:
        log.warning(
            "Found failed files in results",
            count=len(manifest.ResultFiles.FAILED),
            files=[f.Key for f in manifest.ResultFiles.FAILED],
        )

        # Log the failure details from FAILED_0.json if it exists
        try:
            failed_key = f"{input_data.output_prefix}/tt-etl-map-results/{map_run_id}/FAILED_0.json"
            failure_content = s3_client.get_object(failed_key)
            failure_data = json.loads(failure_content.read().decode("utf-8"))
            log.error("Failure details", details=failure_data)
        except Exception as e:
            log.error("Failed to read failure details", error=str(e))

    # Create output zip if there are successful files
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    zip_key = f"{input_data.output_prefix}/processed_files_{timestamp}.zip"

    return create_zip_from_successful_files(
        s3_client, manifest.ResultFiles.SUCCEEDED, zip_key
    )


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
