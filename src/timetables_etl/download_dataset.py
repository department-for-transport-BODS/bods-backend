import io
import json
import os
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

import requests
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.db.manager import DbManager
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
from common_layer.logger import logger
from common_layer.s3 import S3

DT_FORMAT = "%Y-%m-%d_%H-%M-%S"


def bytes_are_zip_file(content: bytes):
    """Returns true if bytes are a zipfile."""
    return zipfile.is_zipfile(io.BytesIO(content))


def get_filetype_from_response(response) -> Optional[str]:

    content_type = response.headers.get("Content-Type", "")
    if "zip" in content_type or bytes_are_zip_file(response.content):
        return "zip"

    if "xml" in content_type:
        return "xml"

    return None


@dataclass
class DownloaderResponse:
    filetype: str
    content: bytes


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


def write_temp_file(url):
    with tempfile.NamedTemporaryFile(delete=False, mode="wb") as temp_file:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
        temp_filename = temp_file.name
    return temp_filename


def upload_file_to_s3(temp_filename, filename, s3_handler):
    with open(temp_filename, "rb") as temp_file_data:
        s3_handler.put_object(filename, temp_file_data.read())


@file_processing_result_to_db(step_name=StepName.DOWNLOAD_DATASET)
def lambda_handler(event, context):
    """
    Main lambda handler
    """
    logger.info(f"Received event:{json.dumps(event, indent=2)}")
    TIME_ZONE = os.environ.get("USE_TZ")
    bucket = event["Bucket"]
    key = event["ObjectKey"]
    url_link = event["URLLink"]

    # Get revision
    revision_id = int(event["DatasetRevisionId"])
    db = DbManager.get_db()
    revision = get_revision(db, revision_id)
    s3_handler = S3(bucket_name=bucket)

    if revision.url_link:
        logger.info("Downloading data.")
        try:
            now = datetime.now(tz=timezone.utc if TIME_ZONE else None).strftime(
                DT_FORMAT
            )
            downloader = DataDownloader(revision.url_link)
            response = downloader.get()
        except DownloadException as exc:
            logger.error(exc.message, exc_info=True)
            raise PipelineException(exc.message) from exc
        else:
            logger.info("Timetables file downloaded successfully.")
            url_path = Path(revision.url_link)
            if url_path.suffix in (".zip", ".xml"):
                name = unquote(url_path.name)
            else:
                name = f"remote_dataset_{revision.dataset.id}_{now}.{response.filetype}"

            temp_file_name = write_temp_file(url_link)
            upload_file_to_s3(temp_file_name, name, s3_handler)
            dataset_revision = DatasetRevisionRepository(db)
            revision = dataset_revision.get_by_id(revision_id)
            revision.upload_file = name
            dataset_revision.update(revision)
        return {"statusCode": 200, "body": f"file downloaded successfully"}
    else:
        logger.info("nothing to download.")
        return {"statusCode": 200, "body": f"nothing to download"}
