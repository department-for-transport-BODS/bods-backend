import io
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from os import environ
from pathlib import Path
from urllib.parse import unquote

import requests
from common_layer.database import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.exceptions.file_exceptions import (
    DownloadException,
    DownloadTimeout,
    UnknownFileType,
)
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from pydantic import AnyUrl, BaseModel, Field
from requests.exceptions import RequestException
from structlog.stdlib import get_logger

DT_FORMAT = "%Y-%m-%d_%H-%M-%S"
log = get_logger()


class DownloadDatasetInputData(BaseModel):
    """
    Input data for the download dataset function
    """

    class Config:
        """
        Allow us to map Bucket / Object Key
        """

        populate_by_name = True

    task_id: int = Field(alias="DatasetEtlTaskResultId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")
    remote_dataset_url_link: AnyUrl = Field(alias="URLLink", default=None)
    revision_id: int = Field(alias="DatasetRevisionId")


@dataclass
class DownloaderResponse:
    """
    Pydantic model that represents the response from a file download operation.

    This model is used to capture the file type (e.g., MIME type or file extension)
    and the binary content of the downloaded file.
    """

    filetype: str
    content: bytes


def bytes_are_zip_file(content: bytes) -> bool:
    """Returns true if bytes are a zipfile."""
    return zipfile.is_zipfile(io.BytesIO(content))


def get_filetype_from_response(response) -> str | None:
    """
    Extract the file type from the HTTP response headers or content.
    """
    content_type = response.headers.get("Content-Type", "")
    if "zip" in content_type or bytes_are_zip_file(response.content):
        return "zip"

    if "xml" in content_type:
        return "xml"

    return None


class DataDownloader:
    """Class to download data files from a url.

    Args:
        url (str): the url hosting the file to download.
        username (str | None): optional username if url requires authentication.
        password (str | None): optional password if url requires authentication.

    Examples:
        # Use download the contents of the url and get the file format.
        >>> downloader = DataDownloader("https://fakeurl.com")
        >>> response = downloader.get()
        >>> response.filetype
            "xml"
        >>> response.content
            b"<Root><Child>hello,world</Child></Root>"
    """

    def __init__(self, url, username=None, password=None):
        self.url = url
        self.password = password
        self.username = username

    def _make_request(self, method, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = 30

        if self.username is None or self.password is None:
            auth = None
        else:
            auth = (self.username, self.password)

        try:
            response = requests.request(method, self.url, auth=auth, **kwargs)
        except requests.Timeout as exc:
            raise DownloadTimeout(self.url) from exc
        except requests.RequestException as exc:
            raise DownloadException(self.url) from exc
        else:
            response.raise_for_status()
            return response

    def get(self, **kwargs) -> DownloaderResponse:
        """Get the response content.

        Args:
            kwargs (dict): Keyword arguments that are passed to requests.request.

        Raises:
            UnknownFileType: if filetype is not xml or zip.
        """
        response = self._make_request("GET", **kwargs)
        if (filetype := get_filetype_from_response(response)) is None:
            raise UnknownFileType(self.url)

        return DownloaderResponse(content=response.content, filetype=filetype)


def write_temp_file(url: str) -> Path | None:
    """
    Download file from a URL to a temporary file.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as temp_file:
            log.info(
                "Starting file download",
                extra={"url": url, "temp_path": temp_file.name},
            )
            with requests.get(url, stream=True, timeout=60) as response:
                log.debug(f"HTTP Response: {response.status_code}, URL: {url}")
                response.raise_for_status()
                log.info(
                    "Response received",
                    extra={"url": url, "status_code": response.status_code},
                )
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        downloaded_size += len(chunk)
                temp_file.flush()
                log.info(
                    "Download completed successfully",
                    extra={
                        "url": url,
                        "temp_path": temp_file.name,
                        "size_bytes": downloaded_size,
                    },
                )
                return Path(temp_file.name)
    except RequestException as exc:
        log.error(
            "Download failed",
            extra={"url": url, "error": str(exc), "error_type": type(exc).__name__},
        )
        raise PipelineException(f"Exception {exc}") from exc


def upload_file_to_s3(temp_filename: str, filename: str, s3_handler: S3) -> None:
    """
    Upload the file to s3 bucket
    """
    with open(temp_filename, "rb") as temp_file_data:
        s3_handler.put_object(filename, temp_file_data.read())


def download_data_from_remote_url(
    revision: OrganisationDatasetRevision,
) -> DownloaderResponse:
    """
    Get the response from the given url and return the pydantic model DownloaderResponse
    """
    try:
        downloader = DataDownloader(revision.url_link)
        response = downloader.get()
        return response
    except DownloadException as exc:
        log.error(exc.message, exc_info=True)
        raise PipelineException(exc.message) from exc


def get_remote_file_name(
    revision: OrganisationDatasetRevision,
    response: DownloaderResponse,
    is_time_zone: bool,
) -> str:
    """
    Create the name for the remote file using the current date and timestamp
    """
    now = datetime.now(tz=timezone.utc if is_time_zone else None).strftime(DT_FORMAT)
    url_path = Path(revision.url_link)
    if url_path.suffix in (".zip", ".xml"):
        name = unquote(url_path.name)
    else:
        name = f"remote_dataset_{revision.dataset.id}_{now}.{response.filetype}"
    return name


def download_and_upload_dataset(
    db: SqlDB, s3_bucket_name: str, revision_id: int, url_link: str, is_time_zone: bool
) -> dict:
    """
    Template function to download the dataset, upload to S3 and update database
    """
    revision = OrganisationDatasetRevisionRepo(db).get_by_id(revision_id)
    s3_handler = S3(bucket_name=s3_bucket_name)
    response = download_data_from_remote_url(revision)
    file_name = get_remote_file_name(revision, response, is_time_zone)
    temp_file_name = write_temp_file(url_link)
    upload_file_to_s3(temp_file_name, file_name, s3_handler)
    update_dataset_revision(revision_id, file_name, db)
    return {"statusCode": 200, "body": "file downloaded successfully"}


def update_dataset_revision(revision_id: int, file_name: str, db: SqlDB) -> None:
    """
    Update the dataset revision in the database with the new file name.
    """
    dataset_revision = OrganisationDatasetRevisionRepo(db)
    revision = dataset_revision.get_by_id(revision_id)
    if revision:
        revision.upload_file = file_name
        dataset_revision.update(revision)
        log.info("Dataset revision updated with new file.")
    else:
        log.info("Dataset revision not found.", revision_id=revision_id)


@file_processing_result_to_db(step_name=StepName.DOWNLOAD_DATASET)
def lambda_handler(event, context) -> dict:
    """
    Main lambda handler
    """
    configure_logging()
    log.debug("Input Data", data=event)
    TIME_ZONE = environ.get("USE_TZ", default=False)
    input_data = DownloadDatasetInputData(**event)
    db = SqlDB()
    if input_data.remote_dataset_url_link:
        return download_and_upload_dataset(
            db,
            input_data.s3_bucket_name,
            input_data.revision_id,
            input_data.remote_dataset_url_link,
            TIME_ZONE,
        )
    else:
        log.info("url link is not specified, nothing to download.")
        return {
            "statusCode": 200,
            "body": "url link is not specified, nothing to download",
        }
