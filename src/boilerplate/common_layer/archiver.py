"""
Module to support different dataset archiving to S3
"""

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from common_layer.database.client import SqlDB
from common_layer.database.models import AvlCavlDataArchive
from common_layer.database.repos import AvlCavlDataArchiveRepo
from common_layer.s3 import S3
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from structlog.stdlib import get_logger

log = get_logger()


class BucketSettings(BaseSettings):
    """Archive bucket settings"""

    model_config = SettingsConfigDict(case_sensitive=False, extra="allow")

    bucket_name: str = Field(
        default="",
        validation_alias="AWS_SIRIVM_STORAGE_BUCKET_NAME",
        description="Name of archive s3 bucket",
    )


class SirivmSettings(BucketSettings):
    """Url settings for sirivm archive"""

    base_url: str = Field(
        default="",
        validation_alias="AVL_CONSUMER_API_BASE_URL",
        description="Avl consumer api base url",
    )

    @property
    def url(self):
        """Get api url to archive data from"""
        return self.base_url


class GtfsrtSettings(BucketSettings):
    """Url settings for gtfsrt archive"""

    cavl_url: str = Field(
        default="", validation_alias="CAVL_CONSUMER_URL", description="Avl consumer url"
    )
    gtfs_url: str = Field(
        default="", validation_alias="GTFS_API_BASE_URL", description="Gtfs base url"
    )
    gtfs_api_active: str = Field(
        default="false",
        validation_alias="GTFS_API_ACTIVE",
        description="State of Gtfs api active or not",
    )

    @property
    def url(self) -> str:
        """Get api url to archive data from"""
        if self.gtfs_api_active == "true":
            return f"{self.gtfs_url}/gtfs-rt"
        return f"{self.cavl_url}/gtfsrtfeed"


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
    bucket_name: str


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


def upload_to_s3(bucket_name: str, filename: str, content: bytes) -> None:
    """Uploads file content to S3 bucket."""
    log.info("Uploading archive file", bucket=bucket_name, filename=filename)
    s3 = S3(bucket_name)
    s3.put_object(filename, content)


def archive_data(archive_details: ArchiveDetails) -> tuple[str, datetime]:
    """Function to fetch and archive."""
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
        upload_to_s3(archive_details.bucket_name, s3_filename, zipped_file.getvalue())

        return s3_filename, current_time

    except Exception as err:
        log.error("Failed to archive the data", url=archive_details.url, exc_info=True)
        raise ArchivingError(
            f"Unable archive the date from url {archive_details.url}"
        ) from err


def process_archive(db: SqlDB, archive_details: ArchiveDetails) -> str:
    """Process the archive and save the data."""

    log.info("Start archiving the data", details=ArchiveDetails)

    start_time = time.time()
    # Archive the data and upload to s3
    file_name, current_time = archive_data(archive_details)
    # Wrtie to db
    upsert_cavl_table(db, archive_details.data_format, file_name, current_time)

    log.info(
        "Finished archiving the data",
        bucket=archive_details.bucket_name,
        file_name=file_name,
        time=time.time() - start_time,
    )

    return file_name
