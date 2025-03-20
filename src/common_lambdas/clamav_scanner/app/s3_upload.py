"""
Post ClamAV Scan, upload files to S3
"""

import asyncio
from pathlib import Path

from common_layer.s3 import (
    S3,
    ProcessingStats,
    process_file_to_s3,
    process_zip_to_s3_async,
)
from structlog.stdlib import get_logger

from .verify_file import verify_zip_file

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

    return f"serverless-extracted-files/{file_stem}/{request_id}/"


def verify_and_extract(
    s3_handler: S3, downloaded_file_path: Path, filename: str, request_id: str
) -> tuple[str, ProcessingStats]:
    """
    Scan and extract eh files
    """
    if downloaded_file_path.suffix.lower() == ".zip":
        verify_zip_file(downloaded_file_path, filename)
    s3_output_folder = make_output_folder_name(downloaded_file_path, request_id)
    generated_prefix = unzip_and_upload_files(
        s3_handler, downloaded_file_path, s3_output_folder
    )
    return generated_prefix


def unzip_and_upload_files(
    s3_handler: S3, file_path: Path, s3_output_folder: str
) -> tuple[str, ProcessingStats]:
    """
    If the file is a zip, unzip and upload its contents to S3.
    Otherwise, copy the single file to a new folder and return that folder path.
    """
    tags = {
        "Lifecycle": "temporary",
        "Expiration": "After ETL Completion",
        "Purpose": "Serverless ETL Map Processing",
    }
    if file_path.suffix.lower() == ".zip":
        log.info("Input File is a Zip. Processing...", file_path=str(file_path))
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            process_zip_to_s3_async(
                s3_client=s3_handler,
                zip_path=file_path,
                destination_prefix=s3_output_folder,
                tags=tags,
                max_concurrent=50,
            )
        )

    log.info("Input file is a single file", path=str(file_path))
    return process_file_to_s3(
        s3_client=s3_handler, file_path=file_path, destination_prefix=s3_output_folder
    )
