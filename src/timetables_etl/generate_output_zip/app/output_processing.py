"""
Functions to create and upload zip files.
"""

import zipfile
from io import BytesIO
from typing import List, Tuple

from common_layer.aws.step import MapExecutionSucceeded
from common_layer.s3 import S3
from structlog.stdlib import get_logger

log = get_logger()

COMPRESSION_TYPE = zipfile.ZIP_DEFLATED
COMPRESSION_LEVEL = 9


def process_single_file(
    s3_client: S3, file: MapExecutionSucceeded
) -> Tuple[BytesIO, str]:
    """
    Process a single file and return it as an XML.

    Args:
        s3_client (S3): S3 client for interacting with AWS S3.
        file (MapExecutionSucceeded): Metadata of the file to process.

    Returns:
        Tuple[BytesIO, str]: A tuple containing the file content as a BytesIO object
        and the filename of the processed file.

    Raises:
        ValueError: If the file is missing parsed input data.
        Exception: If there is an error while processing the file.
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
    except Exception as exc:
        log.error(
            "Failed to process XML file",
            filename=file.parsed_input.Key,
            exc_info=True,
        )
        raise exc


def get_original_zip(s3_client: S3, file_key: str, file_path: str) -> bool:
    """
    Download a zip file from S3 and save it locally.

    Args:
        s3_client: Custom S3 class instance for interacting with AWS S3.
        file_key (str): The key of the zip file in the S3 bucket.
        file_path (str): Local path to save the downloaded zip file.

    Returns:
        bool: True if the file was successfully downloaded, False otherwise.
    """
    try:
        response = s3_client.get_object(file_key)
        filename = file_key.split("/")[-1]
        with open(file_path, "wb") as f:
            for chunk in response:
                f.write(chunk)

        log.info(f"Successfully downloaded {filename} to {file_path}")
        return True

    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error(
            f"Unexpected error while downloading {file_key}: {str(e)}", exc_info=True
        )
        return False


def generate_zip_file(
    s3_client: S3,
    successful_files: List[MapExecutionSucceeded],
    original_object_key: str,
) -> Tuple[BytesIO, int, int]:
    """
    Generate an in-memory zip file containing successfully processed files from a source zip in S3.

    Args:
        s3_client: Custom S3 class instance for interacting with AWS S3.
        successful_files: List of MapExecutionSucceeded objects,
        each containing parsed_input with an S3 Key.
        original_object_key: S3 key of the source zip file to process.

    Returns:
        Optional[BytesIO]: In-memory BytesIO buffer containing the new zip file if successful,

    Raises:
        zipfile.BadZipFile: If the source zip file is invalid or corrupted.
    """
    file_keys = [
        file.parsed_input.Key
        for file in successful_files
        if file.parsed_input and file.parsed_input.Key
    ]

    filename = original_object_key.split("/")[-1]
    file_path = f"/tmp/{filename}"
    zip_count = 0
    failed_count = 0

    try:
        success = get_original_zip(s3_client, original_object_key, file_path)
        if not success:
            log.error(f"Failed to download source zip: {original_object_key}")
            return (BytesIO(), 0, 0)

        zip_file_keys = [key.split("/")[-1] for key in file_keys]

        zip_buffer = BytesIO()
        with zipfile.ZipFile(file_path, "r") as source_zip:
            zip_file_list = source_zip.namelist()
            missing_files = [key for key in zip_file_keys if key not in zip_file_list]
            if missing_files:
                log.error(f"Files not found in source zip: {missing_files}")
                return (BytesIO(), 0, 0)

            with zipfile.ZipFile(
                zip_buffer,
                "w",
                compression=COMPRESSION_TYPE,
                compresslevel=COMPRESSION_LEVEL,
            ) as output_zip:
                for file_key in zip_file_keys:
                    try:
                        log.info(f"Copying {file_key} to new in-memory zip")
                        file_content = source_zip.read(file_key)
                        output_zip.writestr(file_key, file_content)
                        zip_count += 1
                    except (zipfile.BadZipFile, IOError) as e:
                        log.error(
                            f"Failed to add file to zip: {file_key}: {str(e)}",
                            exc_info=True,
                        )
                        failed_count += 1
                        continue

        zip_buffer.seek(0)
        log.info(f"Successfully created in-memory zip with {len(file_keys)} files")
        return (zip_buffer, zip_count, failed_count)

    except zipfile.BadZipFile:
        log.error(f"Invalid zip file: {file_path}", exc_info=True)
        return (BytesIO(), 0, 0)
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error(
            f"Unexpected error while processing {original_object_key}: {str(e)}",
            exc_info=True,
        )
        return (BytesIO(), 0, 0)


def process_files(
    s3_client: S3,
    successful_files: List[MapExecutionSucceeded],
    original_object_key: str,
) -> Tuple[BytesIO, int, int, str]:
    """
    Process files based on count - single file returns XML, multiple files return ZIP.
    Args:
        s3_client (S3): S3 client for interacting with AWS S3.
        successful_files (List[MapExecutionSucceeded]): List of successfully processed files.

    Returns:
        Tuple[BytesIO, int, int, str]: A tuple containing:
        - BytesIO object containing the file content
        - Number of successfully processed files
        - Number of failed files
        - Extension of the output file ('.xml' or '.zip')
    """

    if len(successful_files) == 1:
        file_content, _ = process_single_file(s3_client, successful_files[0])
        return file_content, 1, 0, ".xml"

    log.info("Processing multiple files", file_count=len(successful_files))

    zip_count = 0
    failed_count = 0
    output_zip = generate_zip_file(
        s3_client=s3_client,
        successful_files=successful_files,
        original_object_key=original_object_key,
    )

    log.info(
        "Zipping completed",
        success_count=zip_count,
        failed_count=failed_count,
        output_zip_size=len(output_zip[0].getbuffer()),
    )
    return output_zip, zip_count, failed_count, ".zip"
