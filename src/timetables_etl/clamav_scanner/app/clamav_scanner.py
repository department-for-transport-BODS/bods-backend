"""
Description: Module to scan incoming s3 file object for vulnerabilities.
Lambda handle is triggered by S3 event
"""

import shutil
from pathlib import Path
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .av_scan import av_scan_file, get_clamav_config
from .hashing import calculate_and_update_file_hash
from .models import ClamAVScannerInputData
from .s3_upload import unzip_and_upload_files

log = get_logger()


def make_output_folder_name(
    file_path: Path,
    request_id: str,
) -> str:
    """
    Generate a folder structure based on filename and request ID for easy lookup
    of multiple runs of the same file.
    filename/request_id/
    """
    file_stem = file_path.stem

    return f"{file_stem}/{request_id}/"


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
    downloaded_file_path = s3_handler.download_to_tempfile(
        file_path=input_data.s3_file_key
    )
    s3_output_folder = make_output_folder_name(
        downloaded_file_path, context.aws_request_id
    )
    try:
        # Calculate hash and scan file
        calculate_and_update_file_hash(db, input_data, downloaded_file_path)
        av_scan_file(clam_av_config, downloaded_file_path)

        # Handle zip extraction if needed
        generated_prefix = unzip_and_upload_files(
            s3_handler, downloaded_file_path, s3_output_folder
        )

        msg = (
            f"Successfully scanned the file '{input_data.s3_file_key}' "
            f"from bucket '{input_data.s3_bucket_name}'"
        )

        log.info("Sucessfully processed input file", generated_prefix=generated_prefix)

        return {
            "statusCode": 200,
            "body": {
                "message": msg,
                "generatedPrefix": generated_prefix,
            },
        }

    finally:
        # Clean up the temp file
        shutil.rmtree(Path(downloaded_file_path).parent)
