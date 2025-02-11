"""
Module to support different dataset archiving to S3
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from os import environ
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from common_layer.database.client import SqlDB
from common_layer.database.models import AvlCavlDataArchive
from common_layer.database.repos import AvlCavlDataArchiveRepo
from common_layer.s3 import S3
from structlog.stdlib import get_logger

log = get_logger()


@dataclass
class ArchiveDetails:
    """
    Handle archive details
    """

    url: str
    data_format: str
    file_extension: str
    s3_file_prefix: str
    local_file_prefix: str


class ArchivingError(Exception):
    """
    Exception for Archiving
    """


def upsert_cavl_table(
    db: SqlDB, data_format: str, file_name: str, current_time: datetime
) -> None:
    """Update or insert a record in the database."""
    archive = AvlCavlDataArchiveRepo(db).get_by_data_format(data_format)
    if not archive:
        archive = AvlCavlDataArchive(data_format=data_format, data=file_name)
        archive.last_updated = current_time
        AvlCavlDataArchiveRepo(db).insert(archive)
    else:
        archive.data = file_name
        archive.last_updated = current_time
        AvlCavlDataArchiveRepo(db).update(archive)


def get_content(url: str) -> bytes:
    """Fetches content from a given URL."""
    response = None
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        log.info("Response received", url=url, status_code=response.status_code)
        return response.content

    except requests.exceptions.Timeout as err:
        log.error("Request timed out", url=url)
        raise RuntimeError(f"Request to {url} timed out.") from err

    except requests.exceptions.ConnectionError as err:
        log.error("Network connection error", url=url)
        raise RuntimeError(f"Network error while connecting to {url}.") from err

    except requests.exceptions.HTTPError as err:
        status_code = response.status_code if response is not None else "Unknown"
        log.error("HTTP error occurred", url=url, status_code=status_code)
        raise RuntimeError(
            f"HTTP error {status_code} when accessing {url}: {err}"
        ) from err

    except requests.exceptions.RequestException as err:
        log.error("Failed to fetch data", url=url, error=str(err))
        raise RuntimeError(f"Unable to retrieve data from {url}") from err


def zip_content(content: bytes, filename: str) -> BytesIO:
    """Compress content into a zip file."""
    log.info("Zipping content", filename=filename)
    bytesio = BytesIO()
    with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as zf:
        zf.writestr(filename, content)
    return bytesio


def upload_to_s3(filename: str, content: bytes) -> None:
    """Uploads file content to S3 bucket."""
    bucket_name = environ.get("AWS_SIRIVM_STORAGE_BUCKET_NAME", None)
    if bucket_name:
        log.info("Uploading archive file", bucket=bucket_name, filename=filename)
        s3 = S3(bucket_name)
        s3.put_object(filename, content)
    else:
        log.error("S3 bucket not set")
        raise ValueError("S3 bucket not defined")


def archive_data(archive_details: ArchiveDetails) -> str:
    """Main function to fetch, archive, and save the data."""
    try:
        # Get the content from url
        content = get_content(archive_details.url)

        # Write the content to local file
        local_file_name = (
            f"{archive_details.local_file_prefix}{archive_details.file_extension}"
        )
        zipped_file = zip_content(content, local_file_name)

        # Uploading file to s3
        current_time = datetime.now(timezone.utc)
        s3_filename = (
            f"{archive_details.s3_file_prefix}_"
            f"{current_time.strftime('%Y-%m-%d_%H%M%S')}.zip"
        )
        upload_to_s3(s3_filename, zipped_file.getvalue())

        # Writing to db
        db = SqlDB()
        upsert_cavl_table(db, archive_details.data_format, s3_filename, current_time)
        log.info("Archiving completed", filename=s3_filename)
        return s3_filename
    except Exception as err:
        log.error("Failed to archive the data", url=archive_details.url, exc_info=True)
        raise ArchivingError(
            f"Unable archive the date from url {archive_details.url}"
        ) from err
