"""
Description: Module to scan incoming s3 file object for vulnerabilities.
Lambda handle is triggered by S3 event
"""

import shutil
from pathlib import Path
from typing import Any

import common_layer.aws.datadog.tracing  # type: ignore # pylint: disable=unused-import
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.repos import ETLTaskResultRepo
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.exceptions import S3FileTooLargeError
from common_layer.s3 import S3, get_filename_from_object_key_except
from structlog.stdlib import get_logger

from .av_scan import av_scan_file, get_clamav_config
from .hashing import calculate_and_update_file_hash
from .models import ClamAVScannerInputData
from .s3_upload import verify_and_extract

log = get_logger()


def download_and_verify_s3_file(
    s3_handler: S3, file_key: str, max_size_bytes: int = 400_000_000
) -> Path:
    """
    Check file does not exceed max file size and then download it to temp dir
    """
    file_size = s3_handler.get_file_size(file_key)

    if file_size > max_size_bytes:
        log.error(
            "File Too Large",
            file_key=file_key,
            file_size=file_size,
            max_size=max_size_bytes,
        )
        raise S3FileTooLargeError(file_size=file_size, max_size=max_size_bytes)

    log.info(
        "File Size Check Passed",
        file_key=file_key,
        file_size=file_size,
        max_size=max_size_bytes,
    )

    downloaded_file = s3_handler.download_to_tempfile(file_key)
    return downloaded_file


@file_processing_result_to_db(step_name=StepName.CLAM_AV_SCANNER)
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Main lambda handler
    """
    input_data = ClamAVScannerInputData(**event)
    s3_handler = S3(bucket_name=input_data.s3_bucket_name)
    clam_av_config = get_clamav_config()
    db = SqlDB()
    # Fetch the object from s3
    downloaded_file_path = download_and_verify_s3_file(
        s3_handler, input_data.s3_file_key
    )

    try:
        # Calculate hash and scan file
        calculate_and_update_file_hash(db, input_data, downloaded_file_path)
        av_scan_file(clam_av_config, downloaded_file_path)

        filename = get_filename_from_object_key_except(input_data.s3_file_key)

        generated_prefix, stats = verify_and_extract(
            s3_handler, downloaded_file_path, filename, context.aws_request_id
        )

        msg = (
            f"Successfully scanned the file '{input_data.s3_file_key}' "
            f"from bucket '{input_data.s3_bucket_name}'"
        )

        ETLTaskResultRepo(db).update_progress(input_data.dataset_etl_task_result_id, 40)
        log.info("Sucessfully processed input file", generated_prefix=generated_prefix)

        return {
            "statusCode": 200,
            "body": {
                "message": msg,
                "generatedPrefix": generated_prefix,
                "stats": stats.model_dump(),
            },
        }

    finally:
        # Clean up the temp file
        shutil.rmtree(Path(downloaded_file_path).parent)
