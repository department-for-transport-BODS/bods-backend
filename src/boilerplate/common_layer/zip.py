"""
Zip Handling Utilities
"""

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Generator
from zipfile import BadZipFile, ZipFile, is_zipfile

from botocore.exceptions import ClientError
from common_layer.exceptions.zip_file_exceptions import (
    NestedZipForbidden,
    NoDataFound,
    ZipTooLarge,
    ZipValidationException,
)
from common_layer.s3 import S3
from common_layer.utils import get_file_size
from structlog.stdlib import get_logger

log = get_logger()


@dataclass
class ProcessingStats:
    """
    Zip Extract and Upload to S3 Stats
    """

    success_count: int = 0
    fail_count: int = 0
    skip_count: int = 0


def extract_zip_file(zip_path: Path) -> Generator[tuple[str, Path], None, None]:
    """
    Extract files from zip one at a time to a temporary location
    With cleanup after each to reduce disk space consumption

    Yields:
        Tuple of (original filename, path to extracted file)
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            with ZipFile(zip_path) as zip_obj:
                file_list = [
                    (
                        f.decode("cp437").encode("utf8").decode("utf8")
                        if isinstance(f, bytes)
                        else f
                    )
                    for f in zip_obj.namelist()
                    if not f.endswith("/")
                ]

                for file_path in file_list:
                    extracted_path = Path(temp_dir) / file_path
                    extracted_path.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        with zip_obj.open(file_path) as source, open(
                            extracted_path, "wb"
                        ) as target:
                            shutil.copyfileobj(source, target, length=8192)

                        yield file_path, extracted_path

                    except (OSError, IOError):
                        log.error(
                            "Failed to extract file from zip",
                            file_path=file_path,
                            exc_info=True,
                        )
                        raise
                    finally:
                        try:
                            if extracted_path.exists():
                                os.unlink(extracted_path)
                                log.debug(
                                    "Cleaned up extracted file",
                                    path=str(extracted_path),
                                )
                        except OSError:
                            log.error(
                                "Failed to cleanup extracted file",
                                path=str(extracted_path),
                                exc_info=True,
                            )

        except BadZipFile:
            log.error("Invalid zip file", zip_path=zip_path, exc_info=True)
            raise


def is_xml_file(file_path: str) -> bool:
    """
    Check if a file is an XML file based on its extension.
    """
    return Path(file_path).suffix.lower() == ".xml"


def process_zip_to_s3(s3_client: "S3", zip_path: Path, destination_prefix: str) -> str:
    """Process a zip file and upload its contents to S3."""
    stats = ProcessingStats()

    log.info(
        "Processing zip file", zip_path=str(zip_path), destination=destination_prefix
    )

    try:
        for filename, extracted_path in extract_zip_file(zip_path):
            if not filename.lower().endswith(".xml"):
                log.debug("Skipping non-XML file", filename=filename)
                stats.skip_count += 1
                continue

            s3_key = f"{destination_prefix}{filename}"

            try:
                with open(extracted_path, "rb") as file:
                    s3_client.put_object(s3_key, file.read())

                log.debug(
                    "Successfully uploaded XML file", filename=filename, s3_key=s3_key
                )
                stats.success_count += 1

            except (IOError, ClientError):
                log.error(
                    "Failed to upload file to S3",
                    filename=filename,
                    s3_key=s3_key,
                    exc_info=True,
                )
                stats.fail_count += 1

        log.info(
            "Completed zip processing",
            zip_path=str(zip_path),
            destination=destination_prefix,
            files_processed=stats.success_count,
            files_failed=stats.fail_count,
            files_skipped=stats.skip_count,
        )

        return destination_prefix

    except (OSError, BadZipFile):
        log.error(
            "Critical error processing zip file",
            zip_path=str(zip_path),
            exc_info=True,
        )
        raise
