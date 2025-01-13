"""
Functions to Create and upload zip 
"""

import zipfile
from io import BytesIO

from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .models import MapExecutionSucceeded

log = get_logger()


def generate_zip_file(
    s3_client: S3, successful_files: list[MapExecutionSucceeded]
) -> tuple[BytesIO, int, int]:
    """
    Generate a zip file containing all successfully processed files with optimized XML compression

    Returns:
        tuple containing:
        - BytesIO object containing the zip file
        - Number of successfully added files
        - Number of failed files
    """
    zip_buffer = BytesIO()
    zip_count = 0
    failed_count = 0

    compression_level = 9
    compression_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(
        zip_buffer,
        "w",
        compression=compression_type,
        compresslevel=compression_level,
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
                            compression_type=compression_type,
                            compression_level=compression_level,
                        )
                except Exception:  # pylint: disable=broad-exception-caught
                    log.error(
                        "Failed to Add file to Zip",
                        filename=file.parsed_input.Key,
                        exc_info=True,
                    )
                    failed_count += 1
            else:
                log.warning(
                    "Successful File Missing Parsed Input Data",
                    input_data=file.Input,
                    exc_info=True,
                )

    zip_buffer.seek(0)
    return zip_buffer, zip_count, failed_count
