"""
File Download Functions
"""

import io
import tempfile
import zipfile
from pathlib import Path

import requests
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.exceptions.file_exceptions import (
    DownloadException,
    DownloadTimeout,
    UnknownFileType,
)
from common_layer.exceptions.pipeline_exceptions import PipelineException
from pydantic import AnyUrl
from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from .models import DownloaderResponse

log = get_logger()


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

        if self.username is None or self.password is None:
            auth = None
        else:
            auth = (self.username, self.password)

        try:
            response = requests.request(
                method, self.url, auth=auth, timeout=30, **kwargs
            )
            response.raise_for_status()
            return response
        except requests.Timeout as exc:
            raise DownloadTimeout(self.url) from exc
        except requests.RequestException as exc:
            raise DownloadException(self.url) from exc

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


def download_url_to_tempfile(url: AnyUrl | str) -> Path | None:
    """
    Download file from a URL to a temporary file.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as temp_file:
            log.info("Starting file download", url=url, temp_path=temp_file.name)
            with requests.get(str(url), stream=True, timeout=60) as response:
                response.raise_for_status()
                log.info("Response received", url=url, status_code=response.status_code)
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        downloaded_size += len(chunk)
                temp_file.flush()
                log.info(
                    "Download completed successfully",
                    url=url,
                    temp_path=temp_file.name,
                    size_bytes=downloaded_size,
                )
                return Path(temp_file.name)
    except RequestException as exc:
        log.error(
            "Download failed",
            url=url,
            exc_info=True,
        )
        raise PipelineException(f"Exception {exc}") from exc


def download_revision_linked_file(
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
