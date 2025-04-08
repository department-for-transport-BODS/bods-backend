"""
Tests for DownloadDataset Lambda
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.exceptions import DownloadUnknownFileType
from download_dataset.app.download_dataset import make_remote_file_name
from download_dataset.app.file_download import FileDownloader
from download_dataset.app.models import DownloadResult
from freezegun import freeze_time

from tests.factories.database import OrganisationDatasetRevisionFactory

DT_FORMAT = "%Y-%m-%d_%H-%M-%S"
TEST_ENV_VAR = {
    "PROJECT_ENV": "local",
    "POSTGRES_HOST": "sample_host",
    "POSTGRES_PORT": "1234",
    "POSTGRES_USER": "sample_user",
    "POSTGRES_PASSWORD": "<PASSWORD>",
    "POSTGRES_DB": "test_db",
}


@pytest.mark.parametrize(
    "content_type, content, expected_filetype",
    [
        pytest.param(
            "application/zip",
            b"\x50\x4b\x03\x04",
            "zip",
            id="ZIP file response",
        ),
        pytest.param(
            "application/xml",
            b"<?xml version='1.0' encoding='UTF-8'?>",
            "xml",
            id="XML file response",
        ),
    ],
)
def test_get_no_exception(
    mock_file_downloader: FileDownloader,
    content_type: str,
    content: bytes,
    expected_filetype: str,
):
    """
    Test the FileDownloader for valid file responses.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": content_type}
    mock_response.content = content

    # Mock the requests.get call
    with patch("requests.get") as mock_get:
        mock_get.return_value.__enter__.return_value = mock_response
        result = mock_file_downloader.download_to_temp("https://test.com")

        assert isinstance(result, DownloadResult)
        assert result.filetype == expected_filetype
        assert isinstance(result.path, Path)


@pytest.mark.parametrize(
    "content_type, content",
    [
        pytest.param(
            "text/plain",
            b"Invalid content",
            id="Unknown file response",
        ),
    ],
)
def test_get_exception(
    mock_file_downloader: FileDownloader,
    content_type: str,
    content: str,
):
    """
    Test the FileDownloader for unknown file responses (raises exception).
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": content_type}
    mock_response.content = content

    with patch("requests.get") as mock_get:
        mock_get.return_value.__enter__.return_value = mock_response
        with pytest.raises(DownloadUnknownFileType):
            mock_file_downloader.download_to_temp("https://test.com")


def test_make_remote_file_name():
    dataset_id = 123
    revision_id = 345
    filename = "current.zip"
    m_revision: OrganisationDatasetRevision = (
        OrganisationDatasetRevisionFactory.create_with_id(
            id_number=revision_id,
            dataset_id=dataset_id,
            url_link=f"http://test.com/{filename}",
        )
    )

    now = datetime(2025, 4, 8, 10, 15, 30)
    formatted_datetime = "2025-04-08_10-15-30"
    with freeze_time(now):
        result = make_remote_file_name(m_revision, "zip")
        assert result == f"{dataset_id}_{revision_id}_{formatted_datetime}_{filename}"
