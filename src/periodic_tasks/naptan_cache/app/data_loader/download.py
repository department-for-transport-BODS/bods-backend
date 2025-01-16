"""
Downloading and Extracting a GTFS folder
"""

import os
import tempfile
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import requests
from requests.utils import parse_header_links
from structlog.stdlib import get_logger

log = get_logger()


def validate_url(url: str) -> ParseResult:
    """
    Validate the url
    """
    parsed_url = urlparse(url)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        raise ValueError(f"Invalid URL: {url}")
    return parsed_url


def validate_and_get_output_folder(dest_folder: Path | None = None) -> Path:
    """
    Validate the destination folder. If not provided, use a temporary folder.

    """
    if dest_folder:
        dest_folder = dest_folder.resolve()

        if not dest_folder.is_dir():
            raise ValueError(
                f"The specified output folder '{dest_folder}' is not a valid directory."
            )

        if not os.access(dest_folder, os.W_OK):
            raise PermissionError(
                f"Does not have write permissions to the specified output folder '{dest_folder}'."
            )

    else:
        temp_dir = tempfile.mkdtemp()
        dest_folder = Path(temp_dir)

    log.debug("Selected download destination", path=dest_folder)
    return dest_folder


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> None:
    """
    Ensure that the File extention of the file to download is what we want
    """
    _, extension = os.path.splitext(filename)
    if extension.lower() not in allowed_extensions:
        raise ValueError(f"Unsupported file extension: {extension}")


def validate_file_size(response: requests.Response, max_size: int) -> None:
    """
    Ensure that the file isn't too big
    """
    content_length = int(response.headers.get("Content-Length", 0))
    if content_length > max_size:
        raise ValueError(f"File size exceeds the maximum limit of {max_size} bytes.")


def download_file(
    url: str,
    allowed_extensions: list[str],
    dest_folder: Path | None = None,
    max_size_mb: int = 200,
) -> Path:
    """
    Download a file from the given URL and return the local file path.
    """
    parsed_url = validate_url(url)
    timeout: int = 20
    max_size: int = max_size_mb * 1024 * 1024  # To bytes

    output_folder = validate_and_get_output_folder(dest_folder)

    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            validate_file_size(r, max_size)

            # Check the Content-Disposition header for the filename
            content_disposition = r.headers.get("Content-Disposition")
            if content_disposition:
                filename = parse_header_links(content_disposition)[0]["filename"]
            else:
                filename = os.path.basename(parsed_url.path)

            validate_file_extension(filename, allowed_extensions)
            local_path = output_folder / filename

            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return local_path
    except (requests.Timeout, requests.ConnectionError) as e:
        raise RuntimeError(
            f"Connection error occurred while downloading file from {url}"
        ) from e
    except requests.HTTPError as e:
        raise RuntimeError(
            f"HTTP error occurred while downloading file from {url}"
        ) from e
