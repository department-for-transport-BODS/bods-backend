"""
Test File Download Functions
"""

from io import BytesIO
from pathlib import Path
from typing import Callable, Type
from unittest.mock import MagicMock, patch

import pytest
import requests
from common_layer.exceptions import (
    DownloadException,
    DownloadProxyError,
    DownloadTimeout,
    DownloadUnknownFileType,
)
from download_dataset.app.file_download import (
    FileDownloader,
    download_file,
    get_content_type,
    is_zip_file,
)
from pydantic import AnyUrl

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
def test_is_zip_file(test_input: bytes | Callable[[], bytes], expected: bool):
    """
    Test the `is_zip_file` function with various input types.
    """
    if callable(test_input):
        test_input = test_input()

    file_obj = BytesIO(test_input)
    assert is_zip_file(file_obj) is expected


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
            marks=pytest.mark.xfail(raises=DownloadUnknownFileType),
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
            marks=pytest.mark.xfail(raises=DownloadUnknownFileType),
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
def test_get_content_type(
    content_type: str,
    file_content: bytes,
    expected_filetype: str | None,
) -> None:
    """
    Test content type detection from HTTP responses using both Content-Type headers
    and file content analysis.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": content_type}

    file_obj = BytesIO(file_content)

    if expected_filetype is None:
        with pytest.raises(DownloadUnknownFileType):
            get_content_type(mock_response, file_obj)
    else:
        detected_filetype = get_content_type(mock_response, file_obj)
        assert detected_filetype == expected_filetype


@pytest.mark.parametrize(
    "exception, expected_exception",
    [
        pytest.param(
            requests.Timeout("Connection timed out"),
            DownloadTimeout,
            id="Timeout Error",
        ),
        pytest.param(
            requests.ConnectionError("Connection failed"),
            DownloadException,
            id="Connection Error",
        ),
        pytest.param(
            requests.HTTPError(response=requests.Response()),
            DownloadException,
            id="HTTP Error",
        ),
        pytest.param(
            requests.RequestException("Generic failure"),
            DownloadException,
            id="Generic Request Error",
        ),
        pytest.param(
            requests.exceptions.ProxyError("Proxy error", response=requests.Response()),
            DownloadProxyError,
            id="Proxy Error",
        ),
    ],
)
def test_file_downloader_failures(
    exception: requests.RequestException, expected_exception: Type[Exception]
) -> None:
    """
    Test that FileDownloader properly handles various request exceptions.
    """
    downloader = FileDownloader()
    with patch("requests.get", side_effect=exception):
        with pytest.raises(expected_exception):
            downloader.download_to_temp("https://test.com")


def test_download_file_success():
    """Test successful file download"""
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/zip"}
    mock_response.iter_content.return_value = [create_valid_zip()]

    with patch("requests.get", return_value=mock_response) as mock_get:
        mock_get.return_value.__enter__.return_value = mock_response
        result = download_file(AnyUrl("https://test.com"))

        assert isinstance(result.path, Path)
        assert result.filetype == "zip"
        assert result.size > 0
