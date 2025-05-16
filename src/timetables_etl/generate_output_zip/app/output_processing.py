"""
Functions to create and upload zip files.
"""

import queue
import threading
import zipfile
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Tuple

from common_layer.aws.step import MapExecutionSucceeded
from common_layer.s3 import S3
from structlog.stdlib import get_logger

log = get_logger()


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


def create_zip_file(output_zip_filename: str) -> zipfile.ZipFile:
    """
    Create a new zip file with the desired compression settings.

    Args:
        output_zip_filename (str): The name of the output zip file.

    Returns:
        zipfile.ZipFile: A zip file object.
    """
    compression_level = 9
    compression_type = zipfile.ZIP_DEFLATED
    return zipfile.ZipFile(
        output_zip_filename,
        "w",
        compression=compression_type,
        compresslevel=compression_level,
    )


def add_file_to_zip(
    zip_file: zipfile.ZipFile,
    file_key: str,
    s3_client: S3,
    zip_lock: threading.Lock,
) -> bool:
    """
    Download a file from S3 and add it to the zip file.

    Args:
        zip_file (zipfile.ZipFile): The zip file object.
        file_key (str): The key of the file in the S3 bucket.
        s3_client (S3): S3 client for interacting with AWS S3.
        zip_lock (threading.Lock): A lock to ensure thread-safe access to the zip file.

    Returns:
        bool: True if the file was successfully added to the zip, False otherwise.
    """
    try:
        with s3_client.get_object(file_key) as stream:
            filename = file_key.split("/")[-1]
            with zip_lock:
                zip_file.writestr(filename, stream.read())
                log.info("Added file to zip", filename=filename)
                return True
    except (OSError, IOError, AttributeError):
        log.error(
            "Failed to add file to zip",
            filename=file_key,
            exc_info=True,
        )
        return False


def upload_file_to_s3(
    bucket_name: str, file_name: str, object_name: Optional[str], s3_client: S3
) -> None:
    """
    Upload a file to an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket.
        file_name (str): The local file name to upload.
        object_name (Optional[str]): The name of the object in the S3 bucket.
        s3_client (S3): S3 client for interacting with AWS S3.
    """
    try:
        with open(file_name, "rb") as file_obj:
            s3_client.put_object(
                file_path=object_name or file_name, file_data=file_obj.read()
            )
        log.info(
            "Uploaded file to S3",
            file_name=file_name,
            bucket_name=bucket_name,
            object_name=object_name,
        )
    except (OSError, IOError) as exc:
        log.error("Failed to upload file to S3", file_name=file_name, exc_info=exc)


def generate_zip_file(
    s3_client: S3,
    successful_files: List[MapExecutionSucceeded],
    zip_file: zipfile.ZipFile,
    num_threads: int = 10,
) -> Tuple[int, int]:
    """
    Generate a zip file containing all successfully processed files with optimized XML compression.

    Args:
        s3_client (S3): S3 client for interacting with AWS S3.
        successful_files (List[MapExecutionSucceeded]): List of successfully processed files.
        zip_file (zipfile.ZipFile): The zip file object.
        num_threads (int): Number of threads to use for processing files.

    Returns:
        Tuple[int, int]: A tuple containing the number of successfully added files
        and the number of failed files.
    """
    file_queue: queue.Queue[str] = queue.Queue()
    zip_lock = threading.Lock()
    success_count = 0
    failure_count = 0

    for file in successful_files:
        if file.parsed_input and file.parsed_input.Key:
            file_queue.put(file.parsed_input.Key)

    def worker() -> None:
        nonlocal success_count, failure_count
        while not file_queue.empty():
            try:
                file_key = file_queue.get_nowait()
                if add_file_to_zip(zip_file, file_key, s3_client, zip_lock):
                    success_count += 1
                else:
                    failure_count += 1
                file_queue.task_done()
            except queue.Empty:
                break

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    return success_count, failure_count


def process_files(
    s3_client: S3, successful_files: List[MapExecutionSucceeded]
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

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_zip_filename = f"/tmp/my_large_multizip_{current_time}.zip"
    log.info("Processing multiple files", file_count=len(successful_files))
    zip_file = create_zip_file(output_zip_filename)
    success_count, failed_count = generate_zip_file(
        s3_client=s3_client,
        successful_files=successful_files,
        zip_file=zip_file,
        num_threads=10,
    )
    zip_file.close()
    with open(output_zip_filename, "rb") as file_obj:
        zip_buffer = BytesIO(file_obj.read())
    log.info(
        "Zipping completed",
        success_count=success_count,
        failed_count=failed_count,
        output_zip_filename=output_zip_filename,
    )
    return zip_buffer, success_count, failed_count, ".zip"
