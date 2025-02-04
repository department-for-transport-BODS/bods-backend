"""
Post ClamAV Scan, upload files to S3
"""

from pathlib import Path

from common_layer.s3 import S3
from common_layer.zip import process_zip_to_s3
from structlog.stdlib import get_logger

log = get_logger()


def process_file_to_s3(s3_client: S3, file_path: Path, destination_prefix: str) -> str:
    """
    Copy a single file and upload it to S3 in a dedicated folder.
    State Machine Map does not work on single files, requires a folder
    """
    file_name = file_path.name
    s3_key = f"{destination_prefix}{file_name}"

    log.info(
        "Copying single file into a new folder",
        file_path=str(file_path),
        destination=destination_prefix,
    )

    try:
        with open(file_path, "rb") as file:
            s3_client.put_object(s3_key, file.read())
            log.debug(
                "Successfully uploaded file to new location",
                filename=file_name,
                s3_key=s3_key,
            )

        log.info(
            "Completed file processing",
            file_path=str(file_path),
            destination=destination_prefix,
        )

        return destination_prefix

    except Exception:
        log.error(
            "Failed to copy file to new location",
            file_path=str(file_path),
            s3_key=s3_key,
            exc_info=True,
        )
        raise


def unzip_and_upload_files(
    s3_handler: S3, file_path: Path, s3_output_folder: str
) -> str:
    """
    If the file is a zip, unzip and upload its contents to S3.
    Otherwise, copy the single file to a new folder and return that folder path.
    """
    if file_path.suffix.lower() == ".zip":
        log.info("Input File is a Zip. Processing...", file_path=str(file_path))
        return process_zip_to_s3(
            s3_client=s3_handler,
            zip_path=file_path,
            destination_prefix=s3_output_folder,
        )

    log.info("Input file is a single file", path=str(file_path))
    return process_file_to_s3(
        s3_client=s3_handler, file_path=file_path, destination_prefix=s3_output_folder
    )
