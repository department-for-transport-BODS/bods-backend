"""
Test File Download Functions
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from common_layer.exceptions.file_exceptions import DownloadException, DownloadTimeout
from download_dataset.app.file_download import (
    DataDownloader,
    bytes_are_zip_file,
    download_url_to_tempfile,
    get_filetype_from_response,
)

from .conftest import create_valid_zip


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (create_valid_zip(), True),
        (b"not a zip file", False),
        (b"", False),
        (b"<?xml version='1.0' encoding='UTF-8'?>", False),
    ],
    ids=["Valid ZIP file", "Invalid ZIP file", "Empty content", "XML content"],
)
def test_bytes_are_zip_file(test_input: bytes, expected: bool):
    """
    Test the `bytes_are_zip_file` function with various input types.
    """
    if callable(test_input):
        test_input = test_input()

    assert bytes_are_zip_file(test_input) is expected


@pytest.mark.parametrize(
    "content_type,file_content,expected_filetype",
    [
        pytest.param(
            "application/zip",
            b"not a zip file",
            "zip",
            id="ZIP via Content-Type header",
        ),
        pytest.param(
            "application/xml",
            b"not xml content",
            "xml",
            id="XML via Content-Type header",
        ),
        pytest.param(
            "text/xml",
            b"<?xml version='1.0'?>",
            "xml",
            id="XML via text/xml Content-Type",
        ),
        pytest.param(
            "application/octet-stream",
            create_valid_zip(),
            "zip",
            id="Valid Zip",
        ),
        pytest.param(
            "application/json",
            b"{}",
            None,
            id="Unknown filetype",
        ),
        pytest.param(
            "",
            create_valid_zip(),
            "zip",
            id="ZIP detection without Content-Type",
        ),
        pytest.param(
            "text/plain",
            b"regular content",
            None,
            id="Unsupported Content-Type",
        ),
        pytest.param(
            "application/x-zip-compressed",
            b"not a real zip",
            "zip",
            id="Alternative ZIP Content-Type",
        ),
    ],
)
def test_get_filetype_from_response(
    content_type: str,
    file_content: bytes,
    expected_filetype: str | None,
) -> None:
    """
    Test filetype detection from HTTP responses using both Content-Type headers
    and file content analysis. Verifies correct identification of:
    - ZIP files (via header or content)
    - XML files (via various content types)
    - Unknown/unsupported file types
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": content_type}
    mock_response.content = file_content

    detected_filetype = get_filetype_from_response(mock_response)

    assert detected_filetype == expected_filetype


@pytest.mark.parametrize(
    "exception",
    [
        pytest.param(
            requests.Timeout("Connection timed out"),
            id="Timeout Error",
        ),
        pytest.param(
            requests.ConnectionError("Connection failed"),
            id="Connection Error",
        ),
        pytest.param(
            requests.HTTPError("404 Client Error"),
            id="HTTP Error",
        ),
        pytest.param(
            requests.RequestException("Generic failure"),
            id="Generic Request Error",
        ),
    ],
)
def test_downloader_get_failures(exception: requests.RequestException) -> None:
    """
    Test that DataDownloader.get() properly handles various request exceptions.
    Tests timeout, connection, HTTP, and generic request errors.
    """
    downloader = DataDownloader("https://test.com")
    with patch("requests.request", side_effect=exception):
        with pytest.raises((DownloadTimeout, DownloadException)):
            downloader.get()
