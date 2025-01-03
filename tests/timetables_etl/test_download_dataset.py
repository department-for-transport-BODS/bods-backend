import os
import zipfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import BaseModel

from timetables_etl.download_dataset import (
    DataDownloader,
    DownloadException,
    PipelineException,
    UnknownFileType,
    bytes_are_zip_file,
    download_and_upload_dataset,
    download_data_from_remote_url,
    get_filetype_from_response,
    lambda_handler,
    upload_file_to_s3,
    write_temp_file,
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


class Dataset(BaseModel):
    id: int


class Revision(BaseModel):
    url_link: str
    dataset: Dataset


class Response(BaseModel):
    filetype: str


@pytest.fixture
def mock_revision():
    """Fixture for creating a mock revision"""
    revision = MagicMock()
    revision.url_link = "https://example.com/data.csv"
    return revision


@pytest.fixture
def mock_data_downloader():
    return DataDownloader("https://fakeurl.com")


def test_bytes_are_zip_file_valid_zip():
    """
    Test the `bytes_are_zip_file` function with a valid ZIP file content.
    """
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("test.txt", "This is a test file.")

    zip_buffer.seek(0)
    valid_zip_content = zip_buffer.read()

    assert bytes_are_zip_file(valid_zip_content) is True


def test_bytes_are_zip_file_invalid_zip():
    """
    Test the `bytes_are_zip_file` function with a invalid ZIP file content.
    """
    invalid_zip_content = b"not a zip file"
    assert bytes_are_zip_file(invalid_zip_content) is False


def test_bytes_are_zip_file_empty():
    """
    Test the `bytes_are_zip_file` function with a empty ZIP file content.
    """
    empty_content = b""
    assert bytes_are_zip_file(empty_content) is False


def test_bytes_are_zip_file_xml():
    """
    Test the `bytes_are_zip_file` function with a valid xml file content.
    """
    xml_content = b"<?xml version='1.0' encoding='UTF-8'?>"
    assert bytes_are_zip_file(xml_content) is False


def test_get_filetype_from_response_zip():
    """
    Test the `get_filetype_from_response` function with a ZIP file response.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/zip"}
    mock_response.content = b"\x50\x4b\x03\x04"  # Start of a zip file
    assert get_filetype_from_response(mock_response) == "zip"


def test_get_filetype_from_response_xml():
    """
    Test the `get_filetype_from_response` function with a xml file response.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/xml"}
    mock_response.content = b"<?xml version='1.0' encoding='UTF-8'?>"
    assert get_filetype_from_response(mock_response) == "xml"


def test_get_filetype_from_response_unknown():
    """
    Test the `get_filetype_from_response` function with a unknown file response.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b"{}"
    assert get_filetype_from_response(mock_response) is None


def test_get_filetype_from_response_zip_by_content():
    """
    Test the `get_filetype_from_response` function with a ZIP file response.
    """
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("test.txt", "This is a test file.")

    zip_buffer.seek(0)
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = zip_buffer.read()
    result = get_filetype_from_response(mock_response)
    assert result == "zip"


def test_get_zip(mock_data_downloader):
    """
    Test the `get` method of the `mock_data_downloader` to handle ZIP file responses.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/zip"}
    mock_response.content = b"\x50\x4b\x03\x04"
    mock_data_downloader._make_request = MagicMock(return_value=mock_response)

    result = mock_data_downloader.get()
    assert result.filetype == "zip"
    assert result.content == b"\x50\x4b\x03\x04"


def test_get_xml(mock_data_downloader):
    """
    Test the `get` method of the `mock_data_downloader` to handle xml file responses.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/xml"}
    mock_response.content = b"<?xml version='1.0' encoding='UTF-8'?>"
    mock_data_downloader._make_request = MagicMock(return_value=mock_response)

    result = mock_data_downloader.get()
    assert result.filetype == "xml"
    assert result.content == b"<?xml version='1.0' encoding='UTF-8'?>"


def test_get_unknown_filetype(mock_data_downloader):
    """
    Test the `get` method of the `mock_data_downloader` to handle unknown file responses.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.content = b"Invalid content"
    mock_data_downloader._make_request = MagicMock(return_value=mock_response)

    with pytest.raises(UnknownFileType):
        mock_data_downloader.get()


@patch("requests.get")
def test_write_temp_file_timeout(mock_get):
    mock_get.side_effect = requests.exceptions.Timeout

    with pytest.raises(PipelineException):
        write_temp_file("https://fakeurl.com")


@patch("builtins.open", new_callable=MagicMock)
@patch("timetables_etl.download_dataset.S3.put_object")
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


@patch("common_layer.db.file_processing_result.DbManager")
@patch.dict("os.environ", TEST_ENV_VAR)
def test_lambda_handler_no_url_link(mock_DbManager):
    """
    Test the `lambda_hanlder` method to with no url link
    """
    mock_db_instance = MagicMock()
    mock_event = {
        "Bucket": "my-bucket",
        "ObjectKey": "file.zip",
        "DatasetRevisionId": 1,
        "DatasetEtlTaskResultId": "1234",
    }
    mock_context = MagicMock()
    mock_db_instance = MagicMock()
    mock_DbManager.get_db.return_value = mock_db_instance
    response = lambda_handler(mock_event, mock_context)

    assert response["statusCode"] == 200
    assert response["body"] == "nothing to download"


@patch("common_layer.db.file_processing_result.DbManager")
@patch.dict("os.environ", TEST_ENV_VAR)
def test_lambda_handler_invalid_url_link(mock_DbManager):
    """
    Test the `lambda_hanlder` method to with no url link
    """
    mock_db_instance = MagicMock()
    mock_event = {
        "Bucket": "my-bucket",
        "ObjectKey": "file.zip",
        "DatasetRevisionId": 1,
        "DatasetEtlTaskResultId": "1234",
        "URLLink": "//fakeurl.com/file.zip",
    }
    mock_context = MagicMock()
    mock_db_instance = MagicMock()
    mock_DbManager.get_db.return_value = mock_db_instance
    with pytest.raises(ValueError) as exc_info:
        lambda_handler(mock_event, mock_context)


@patch("timetables_etl.download_dataset.download_and_upload_dataset")
@patch("common_layer.db.file_processing_result.DbManager")
@patch.dict("os.environ", TEST_ENV_VAR)
def test_lambda_handler(mock_DbManager, mock_download_upload_dataset):
    """
    Test the `lambda_hanlder` method to with valid url link
    """
    mock_event = {
        "Bucket": "my-bucket",
        "ObjectKey": "file.zip",
        "URLLink": "https://fakeurl.com/file.zip",
        "DatasetRevisionId": 1,
        "DatasetEtlTaskResultId": "1234",
    }
    mock_context = MagicMock()
    mock_db_instance = MagicMock()
    mock_DbManager.get_db.return_value = mock_db_instance
    mock_response = {"statusCode": 200, "body": "file downloaded successfully"}
    mock_download_upload_dataset.return_value = mock_response

    response = lambda_handler(mock_event, mock_context)

    assert response["statusCode"] == 200
    assert response["body"] == "file downloaded successfully"


@patch("timetables_etl.download_dataset.S3")
@patch("common_layer.db.file_processing_result.DbManager.get_db")
@patch("timetables_etl.download_dataset.DatasetRevisionRepository")
@patch("timetables_etl.download_dataset.download_data_from_remote_url")
@patch("timetables_etl.download_dataset.get_remote_file_name")
@patch("timetables_etl.download_dataset.write_temp_file")
@patch("timetables_etl.download_dataset.upload_file_to_s3")
@patch("timetables_etl.download_dataset.update_dataset_revision")
def test_download_and_upload_dataset(
    mock_update_dataset_revision,
    mock_upload_file_to_s3,
    mock_write_temp_file,
    mock_get_remote_file_name,
    mock_download_data_from_remote_url,
    mock_dataset_revision_repo,
    mock_get_db,
    mock_s3,
):
    """
    Test the `download_and_upload_dataset` method to download the file from url and update the db object
    """
    EXPECTED_RESPONSE = {"body": "file downloaded successfully", "statusCode": 200}
    mock_get_db.return_value = MagicMock()
    mock_s3.return_value = MagicMock()
    mock_dataset_revision_repo.return_value = MagicMock()
    input_data = MagicMock()
    input_data.revision_id = 123
    input_data.remote_dataset_url_link = "https://example.com/dataset.csv"
    input_data.s3_bucket_name = "test-bucket"

    mock_download_data_from_remote_url.return_value = {
        "url": "https://example.com/dataset.csv"
    }
    mock_get_remote_file_name.return_value = "some_file_name"
    mock_write_temp_file.return_value = "/tmp/tempfile"

    response = download_and_upload_dataset(input_data, False)

    assert response == EXPECTED_RESPONSE
    mock_upload_file_to_s3.assert_called_once_with(
        "/tmp/tempfile", "some_file_name", mock_s3.return_value
    )
    mock_update_dataset_revision.assert_called_once()


def test_download_data_success(mock_revision):
    """Test successful download case"""
    mock_response = MagicMock()
    mock_response.content = b"fake data"
    with patch.object(DataDownloader, "get", return_value=mock_response) as mock_get:
        response = download_data_from_remote_url(mock_revision)
        mock_get.assert_called_once()
        assert response == mock_response


def test_download_data_failure(mock_revision):
    """Test failure case where DownloadException is raised"""
    with patch.object(
        DataDownloader, "get", side_effect=DownloadException("Download failed")
    ) as mock_get:
        with pytest.raises(PipelineException, match="Download failed"):
            download_data_from_remote_url(mock_revision)
        mock_get.assert_called_once()
