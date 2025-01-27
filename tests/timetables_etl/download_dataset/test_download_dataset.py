"""
Tests for DownloadDataset Lambda
"""

from unittest.mock import MagicMock, patch

import pytest
from common_layer.exceptions.file_exceptions import UnknownFileType

from timetables_etl.download_dataset.app.download_dataset import (
    lambda_handler,
    upload_file_to_s3,
)

DT_FORMAT = "%Y-%m-%d_%H-%M-%S"
TEST_ENV_VAR = {
    "PROJECT_ENV": "dev",
    "POSTGRES_HOST": "sample_host",
    "POSTGRES_PORT": "1234",
    "POSTGRES_USER": "sample_user",
    "POSTGRES_PASSWORD": "<PASSWORD>",
    "TXC_XSD_PATH": "TransXChange_general.xsd",
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
    mock_data_downloader, content_type, content: bytes, expected_filetype: str
):
    """
    Test the `get` method of the `mock_data_downloader` for valid file responses.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": content_type}
    mock_response.content = content
    mock_data_downloader._make_request = MagicMock(return_value=mock_response)
    result = mock_data_downloader.get()
    assert result.filetype == expected_filetype
    assert result.content == content


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
def test_get_exception(mock_data_downloader, content_type, content):
    """
    Test the `get` method of the `mock_data_downloader`
    For unknown file responses (raises exception).
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": content_type}
    mock_response.content = content
    mock_data_downloader._make_request = MagicMock(return_value=mock_response)

    with pytest.raises(UnknownFileType):
        mock_data_downloader.get()


@patch("builtins.open", new_callable=MagicMock)
@patch("timetables_etl.download_dataset.app.download_dataset.S3.put_object")
def test_upload_file_to_s3(mock_put, mock_open):
    """
    Test the `upload_file_to_s3` method to upload file to s3
    """
    mock_file = MagicMock()
    mock_file.read.return_value = b"file content"
    mock_open.return_value.__enter__.return_value = mock_file
    mock_open.return_value.__exit__.return_value = None
    mock_s3_handler = MagicMock()

    temp_filename = "fakefile.tmp"
    filename = "fakefile.txt"

    upload_file_to_s3(temp_filename, filename, mock_s3_handler)
    mock_open.assert_called_once_with(temp_filename, "rb")
    mock_file.read.assert_called_once()


@pytest.mark.parametrize(
    "event, expected_status_code, expected_body",
    [
        pytest.param(
            {
                "Bucket": "my-bucket",
                "ObjectKey": "file.zip",
                "URLLink": "https://fakeurl.com/file.zip",
                "DatasetRevisionId": 1,
                "DatasetEtlTaskResultId": "1234",
            },
            200,
            "file downloaded successfully",
            id="Valid URL Link",
        ),
    ],
)
@patch("common_layer.db.file_processing_result.SqlDB")
@patch(
    "timetables_etl.download_dataset.app.download_dataset.download_and_upload_dataset"
)
@patch.dict("os.environ", TEST_ENV_VAR)
def test_lambda_handler_no_exception(
    mock_download_upload_dataset,
    mock_sqldb,
    event,
    expected_status_code,
    expected_body,
):
    """
    Test the `lambda_handler` method when no exception is raised.
    """
    mock_db_instance = MagicMock()
    mock_sqldb.get_db.return_value = mock_db_instance
    mock_response = {"statusCode": 200, "body": expected_body}
    mock_download_upload_dataset.return_value = mock_response
    mock_context = MagicMock()

    response = lambda_handler(event, mock_context)

    assert response["statusCode"] == expected_status_code
    assert response["body"] == expected_body
