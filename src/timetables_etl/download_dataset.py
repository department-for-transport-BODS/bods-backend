import io
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from os import environ
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

import requests
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.db.manager import BodsDB, DbManager
from common_layer.db.models import OrganisationDatasetrevision
from common_layer.db.repositories.dataset_revision import (
    DatasetRevisionRepository,
    get_revision,
)
from common_layer.exceptions.file_exceptions import (
    DownloadException,
    DownloadTimeout,
    PermissionDenied,
    UnknownFileType,
)
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from pydantic import BaseModel, Field
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
    remote_dataset_url_link: str = Field(alias="URLLink", default=None)
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


def get_filetype_from_response(response) -> Optional[str]:
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

    def raise_for_status(self, response):
        """Check the requests.Response code and raise a downloader exception.

        Args:
            response (Response): a requests.Response object.

        Raises:
            PermissionDenied: if status_code is 401 or 403
            DownloadException: if status_code is greater than 400 but not 401 or 403.

        """
        status_code = response.status_code
        if status_code in [401, 403]:
            raise PermissionDenied(self.url)
        elif status_code > 400:
            message = f"Unable to download from {self.url} with code {status_code}."
            raise DownloadException(self.url, message)

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
            self.raise_for_status(response)
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


def write_temp_file(url: str) -> str:
    """
    Download a file from a given URL and write its content to a temporary file.
    """
    with tempfile.NamedTemporaryFile(delete=False, mode="wb") as temp_file:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
        temp_filename = temp_file.name
    return temp_filename


def upload_file_to_s3(temp_filename: str, filename: str, s3_handler: S3) -> None:
    """
    Upload the file to s3 bucket
    """
    with open(temp_filename, "rb") as temp_file_data:
        s3_handler.put_object(filename, temp_file_data.read())


def download_data_from_remote_url(
    revision: OrganisationDatasetrevision,
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
    revision: OrganisationDatasetrevision,
    response: DownloaderResponse,
    is_time_zone: bool,
) -> str:
    """
    create the name for the remote file using the current date and timestamp
    """
    now = datetime.now(tz=timezone.utc if is_time_zone else None).strftime(DT_FORMAT)
    url_path = Path(revision.url_link)
    if url_path.suffix in (".zip", ".xml"):
        name = unquote(url_path.name)
    else:
        name = f"remote_dataset_{revision.dataset.id}_{now}.{response.filetype}"
    return name


def download_and_upload_dataset(
    input_data: DownloadDatasetInputData, is_time_zone: bool
) -> dict:
    """
    Template function to download the dataset, upload to S3 and update database
    """
    db = DbManager.get_db()
    revision = get_revision(db, input_data.revision_id)
    s3_handler = S3(bucket_name=input_data.s3_bucket_name)
    response = download_data_from_remote_url(revision)
    file_name = get_remote_file_name(revision, response, is_time_zone)
    temp_file_name = write_temp_file(input_data.remote_dataset_url_link)
    upload_file_to_s3(temp_file_name, file_name, s3_handler)
    update_dataset_revision(input_data.revision_id, file_name, db)
    return {"statusCode": 200, "body": "file downloaded successfully"}


def update_dataset_revision(revision_id: int, file_name: str, db: BodsDB) -> None:
    """
    Update the dataset revision in the database with the new file name.
    """
    dataset_revision = DatasetRevisionRepository(db)
    revision = dataset_revision.get_by_id(revision_id)
    revision.upload_file = file_name
    dataset_revision.update(revision)
    log.info("Dataset revision updated with new file.")


@file_processing_result_to_db(step_name=StepName.DOWNLOAD_DATASET)
def lambda_handler(event, context) -> dict:
    """
    Main lambda handler
    """
    configure_logging()
    log.debug("Input Data", data=event)
    TIME_ZONE = environ.get("USE_TZ", default=False)
    input_data = DownloadDatasetInputData(**event)
    if input_data.remote_dataset_url_link:
        return download_and_upload_dataset(input_data, TIME_ZONE)
    else:
        log.info("nothing to download.")
        return {"statusCode": 200, "body": "nothing to download"}
