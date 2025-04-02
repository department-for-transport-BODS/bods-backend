"""
File Download Functions
"""

import tempfile
from pathlib import Path
from typing import BinaryIO
from zipfile import is_zipfile

import requests
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.exceptions import (
    DownloadException,
    DownloadFileNotFound,
    DownloadPermissionDenied,
    DownloadProxyError,
    DownloadTimeout,
    DownloadUnknownFileType,
)
from pydantic import AnyUrl
from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from .models import DownloadResult, FileType

log = get_logger()


def is_zip_file(file: BinaryIO) -> bool:
    """Check if the given file is a valid ZIP file."""
    return is_zipfile(file)


def get_content_type(response: requests.Response, file: BinaryIO) -> FileType:
    """
    Determine content type from headers and file content.
    Returns the FileType ("zip" or "xml") directly.
    """
    content_type = response.headers.get("Content-Type", "").lower()

    if "zip" in content_type or is_zip_file(file):
        return "zip"
    if "xml" in content_type:
        return "xml"
    raise DownloadUnknownFileType(str(response.url))


def validate_filetype(content_type: FileType) -> bool:
    """Validate that the content type is supported."""
    return content_type in {"zip", "xml"}


class FileDownloader:
    """Handles file downloads with error handling and validation."""

    def __init__(self, chunk_size: int = 8192, timeout: int = 60):
        self.chunk_size = chunk_size
        self.timeout = timeout

    def download_to_temp(self, url: str | AnyUrl) -> DownloadResult:
        """Download file to temporary location with validation."""
        url_str = str(url)
        temp_file = Path(tempfile.mktemp())

        try:
            log.info("Starting file download", url=url_str, temp_path=temp_file)

            with requests.get(url_str, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                downloaded_size = self._save_to_file(response, temp_file)

                with open(temp_file, "rb") as f:
                    filetype = get_content_type(response, f)

                log.info(
                    "Download completed successfully",
                    url=url_str,
                    temp_path=temp_file,
                    size_bytes=downloaded_size,
                    filetype=filetype,
                )

                return DownloadResult(
                    path=temp_file, filetype=filetype, size=downloaded_size
                )

        except requests.Timeout as exc:
            self._cleanup_on_error(temp_file, url_str)
            raise DownloadTimeout(
                url=url_str,
                timeout=self.timeout,
            ) from exc
        except requests.exceptions.ProxyError as exc:
            self._cleanup_on_error(temp_file, url_str)
            raise DownloadProxyError(url=url_str, response=str(exc.response)) from exc
        except requests.HTTPError as exc:
            if exc.response.status_code == 403:
                self._cleanup_on_error(temp_file, url_str)
                raise DownloadPermissionDenied(
                    url=url_str,
                ) from exc
            if exc.response.status_code == 404:
                self._cleanup_on_error(temp_file, url_str)
                raise DownloadFileNotFound(url=url_str) from exc
            self._cleanup_on_error(temp_file, url_str)
            raise DownloadException(
                url=url_str,
                reason=exc.response.reason,
                status_code=exc.response.status_code,
            ) from exc

        except RequestException as exc:
            self._cleanup_on_error(temp_file, url_str)
            raise DownloadException(
                url=url_str,
            ) from exc

    def _save_to_file(self, response: requests.Response, path: Path) -> int:
        """Save response content to file and return size."""
        downloaded_size = 0
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
        return downloaded_size

    def _cleanup_on_error(self, path: Path, url: str):
        """Clean up temporary file on error."""
        log.error("Download failed", url=url, exc_info=True)
        if path.exists():
            path.unlink()


def download_file(url: AnyUrl) -> DownloadResult:
    """
    Downloads a file to a temp location
    """
    downloader = FileDownloader()
    return downloader.download_to_temp(url)


def download_revision_linked_file(
    revision: OrganisationDatasetRevision,
) -> DownloadResult:
    """Download file from revision URL to a temporary file."""
    downloader = FileDownloader()
    return downloader.download_to_temp(revision.url_link)
