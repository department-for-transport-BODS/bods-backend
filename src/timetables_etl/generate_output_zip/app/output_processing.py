"""
Functions to Create and upload zip 
"""

import zipfile
from io import BytesIO

from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .models import MapExecutionSucceeded

log = get_logger()


def process_single_file(
    s3_client: S3, file: MapExecutionSucceeded
) -> tuple[BytesIO, str]:
    """
    Process a single file and return it as an XML

    Returns:
        tuple containing:
        - BytesIO object containing the file content
        - filename of the processed file
    """
    if not file.parsed_input or not file.parsed_input.Key:
        log.warning(
            "File Missing Parsed Input Data",
            input_data=file.Input,
            exc_info=True,
        )
        raise ValueError("File missing parsed input data")

    try:
        with s3_client.get_object(file.parsed_input.Key) as stream:
            file_content = BytesIO(stream.read())
            filename = file.parsed_input.Key.split("/")[-1]
            log.info(
                "Processed single XML file",
                filename=filename,
            )
            return file_content, filename
    except Exception as e:
        log.error(
            "Failed to process XML file",
            filename=file.parsed_input.Key,
            exc_info=True,
        )
        raise e


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


def process_files(
    s3_client: S3, successful_files: list[MapExecutionSucceeded]
) -> tuple[BytesIO, int, int, str]:
    """
    Process files based on count - single file returns XML, multiple files returns ZIP

    Returns:
        tuple containing:
        - BytesIO object containing the file content
        - Number of successfully processed files
        - Number of failed files
        - Extension of the output file ('.xml' or '.zip')
    """
    if len(successful_files) == 1:
        file_content, _ = process_single_file(s3_client, successful_files[0])
        return file_content, 1, 0, ".xml"

    zip_content, success_count, failed_count = generate_zip_file(
        s3_client, successful_files
    )
    return zip_content, success_count, failed_count, ".zip"
