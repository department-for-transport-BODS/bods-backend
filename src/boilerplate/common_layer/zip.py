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

                    except Exception as e:
                        log.error(
                            "Failed to extract file from zip",
                            file_path=file_path,
                            error=str(e),
                        )
                        raise
                    finally:
                        # Clean up the extracted file after it's been processed
                        try:
                            if extracted_path.exists():
                                os.unlink(extracted_path)
                                log.debug(
                                    "Cleaned up extracted file",
                                    path=str(extracted_path),
                                )
                        except Exception as e:
                            log.error(
                                "Failed to cleanup extracted file",
                                path=str(extracted_path),
                                error=str(e),
                            )

        except BadZipFile as e:
            log.error("Invalid zip file", zip_path=zip_path, error=str(e))
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

            except Exception:  # pylint: disable=broad-exception-caught
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

    except Exception:
        log.error(
            "Critical error processing zip file",
            zip_path=str(zip_path),
            exc_info=True,
        )
        raise


class ZippedValidator:
    """Class for validating a transxchange zip file.

    Args:
        file (File): a zip file that requires validation.
        max_file_size (int): maximum size a file can be and pass validation.

    Examples:
        # Use the validator to basic validation, e.g. file size, nesting
        >>> f = open("path/to/zip/file.zip", "rb")
        >>> validator = ZippedValidator(f)
        >>> validator.validate()
        >>> f.close()
    """

    def __init__(self, file, max_file_size=1e10, data_file_ext=".xml"):
        self.file = file
        self.file.seek(0)
        self.max_file_size = max_file_size
        self.data_file_ext = data_file_ext
        self.zip_file = ZipFile(self.file)

    def __enter__(self):
        self.zip_file = ZipFile(self.file)
        return self

    def __exit__(self, *args):
        self.zip_file.close()

    def is_valid(self):
        """
        Runs Validator
        """
        try:
            self.validate()
        except ZipValidationException:
            return False

        return True

    def validate(self):
        """Validates a zip file and raises an exception if file is invalid.

        Raises:
            NestedZipForbidden: if zip file contains another zip file.
            ZipTooLarge: if zip file or sum of uncompressed files are
            greater than max_file_size.
            NoDataFound: if zip file contains no files with data_file_ext extension.
        """
        if self.is_nested_zip():
            raise NestedZipForbidden(self.file.name)

        if self.is_too_large() or self.exceeds_uncompressed_size():
            raise ZipTooLarge(self.file.name)

        if not self.has_data():
            raise NoDataFound(self.file.name)

    def is_too_large(self):
        """Returns True if zip file is greater than max_file_size."""
        return get_file_size(self.file) > self.max_file_size

    def is_nested_zip(self):
        """Returns True if zip file contains another zip file."""
        names = self.get_files(extension=".zip")
        # explicity check is_zipfile not just the extension
        for name in names:
            with self.open(name) as m:
                if name.endswith(".zip") or is_zipfile(m):
                    return True
        return False

    def has_data(self):
        """Returns True if zip file contains a file with an data_file_ext extension."""
        return len(self.get_files(extension=self.data_file_ext)) > 0

    def exceeds_uncompressed_size(self):
        """Returns True if the sum of the uncompressed files exceeds max_file_size."""
        total = sum([zinfo.file_size for zinfo in self.zip_file.filelist])
        return total > self.max_file_size

    def open(self, name):
        """Opens zip_file."""
        return self.zip_file.open(name, "r")

    def get_files(self, extension=".xml"):
        """Returns a list of the full paths to the files in zip file.

        Args:
            extension (str): The extension to filter the files on.

        """
        return [name for name in self.zip_file.namelist() if name.endswith(extension)]
