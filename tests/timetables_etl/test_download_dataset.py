import os
import zipfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
import requests

from timetables_etl.download_dataset import (
    DataDownloader,
    UnknownFileType,
    bytes_are_zip_file,
    get_filetype_from_response,
    lambda_handler,
    upload_file_to_s3,
    write_temp_file,
)

TEST_ENV_VAR = {
    "PROJECT_ENV": "dev",
    "POSTGRES_HOST": "sample_host",
    "POSTGRES_PORT": "1234",
    "POSTGRES_USER": "sample_user",
    "POSTGRES_PASSWORD": "<PASSWORD>",
    "TXC_XSD_PATH": "TransXChange_general.xsd",
    "POSTGRES_DB": "test_db",
}

def test_bytes_are_zip_file_valid_zip():
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('test.txt', 'This is a test file.')

    zip_buffer.seek(0)
    valid_zip_content = zip_buffer.read()

    assert bytes_are_zip_file(valid_zip_content) is True

def test_bytes_are_zip_file_invalid_zip():
    invalid_zip_content = b"not a zip file"
    assert bytes_are_zip_file(invalid_zip_content) is False

def test_bytes_are_zip_file_empty():
    empty_content = b""
    assert bytes_are_zip_file(empty_content) is False

def test_bytes_are_zip_file_xml():
    xml_content = b"<?xml version='1.0' encoding='UTF-8'?>"
    assert bytes_are_zip_file(xml_content) is False

def test_get_filetype_from_response_zip():
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/zip"}
    mock_response.content = b"\x50\x4b\x03\x04"  # Start of a zip file
    assert get_filetype_from_response(mock_response) == "zip"

def test_get_filetype_from_response_xml():
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/xml"}
    mock_response.content = b"<?xml version='1.0' encoding='UTF-8'?>"
    assert get_filetype_from_response(mock_response) == "xml"

def test_get_filetype_from_response_unknown():
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b"{}"
    assert get_filetype_from_response(mock_response) is None

def test_get_filetype_from_response_zip_by_content():
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('test.txt', 'This is a test file.')

    zip_buffer.seek(0)
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = zip_buffer.read()
    result = get_filetype_from_response(mock_response)
    assert result == "zip"


@pytest.fixture
def mock_data_downloader():
    return DataDownloader("https://fakeurl.com")

def test_get_zip(mock_data_downloader):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/zip"}
    mock_response.content = b"\x50\x4b\x03\x04"
    mock_data_downloader._make_request = MagicMock(return_value=mock_response)
    
    result = mock_data_downloader.get()
    assert result.filetype == "zip"
    assert result.content == b"\x50\x4b\x03\x04"

def test_get_xml(mock_data_downloader):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/xml"}
    mock_response.content = b"<?xml version='1.0' encoding='UTF-8'?>"
    mock_data_downloader._make_request = MagicMock(return_value=mock_response)
    
    result = mock_data_downloader.get()
    assert result.filetype == "xml"
    assert result.content == b"<?xml version='1.0' encoding='UTF-8'?>"

def test_get_unknown_filetype(mock_data_downloader):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.content = b"Invalid content"
    mock_data_downloader._make_request = MagicMock(return_value=mock_response)
    
    with pytest.raises(UnknownFileType):
        mock_data_downloader.get()


@patch("requests.get")
def test_write_temp_file(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"file content"]
    mock_get.return_value = mock_response
    temp_filename = write_temp_file("https://fakeurl.com")

    with open(temp_filename, "rb") as f:
        content = f.read()
        assert content == b"file content", f"Expected 'file content', but got {content}"
    os.remove(temp_filename)


@patch("builtins.open", new_callable=MagicMock)
@patch("timetables_etl.download_dataset.S3.put_object")
def test_upload_file_to_s3(mock_put, mock_open):
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
def test_lambda_handler_no_url_link(mock_db_manager):
    mock_db_instance = MagicMock()
    mock_db_manager.get_db.return_value = mock_db_instance
    mock_event = {
        "Bucket": "my-bucket",
        "ObjectKey": "file.zip",
        "DatasetRevisionId": 1
    }
    mock_context = MagicMock()
    response = lambda_handler(mock_event, mock_context)

    assert response["statusCode"] == 200
    assert response["body"] == "nothing to download"


@patch("timetables_etl.download_dataset.DataDownloader.get")
@patch("timetables_etl.download_dataset.write_temp_file")
@patch("timetables_etl.download_dataset.upload_file_to_s3")
@patch("timetables_etl.download_dataset.get_revision")
@patch("timetables_etl.download_dataset.DatasetRevisionRepository")
@patch("requests.get")
@patch("common_layer.db.file_processing_result.DbManager")
@patch.dict("os.environ", TEST_ENV_VAR)
def test_lambda_handler(mock_requests_get, mock_DbManager, mock_DatasetRevisionRepository, mock_get_revision, mock_upload, mock_write, mock_get):
    mock_event = {
        "Bucket": "my-bucket",
        "ObjectKey": "file.zip",
        "URLLink": "https://fakeurl.com/file.zip",
        "DatasetRevisionId": 1
    }
    mock_context = MagicMock()
    mock_revision = MagicMock()
    mock_revision.id = 1
    mock_revision.url_link = "https://fakeurl.com/file.zip"
    mock_revision.dataset.id = 123
    mock_get_revision.return_value = mock_revision
    mock_DatasetRevisionRepository.return_value.get_by_id.return_value = mock_revision
    mock_get.return_value = MagicMock(filetype="zip", content=b"\x50\x4b\x03\x04")
    mock_write.return_value = "/tmp/file.zip"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake content"
    mock_requests_get.return_value = mock_response

    mock_update = MagicMock()
    mock_DatasetRevisionRepository.return_value.update = mock_update

    mock_db_instance = MagicMock()
    mock_DbManager.get_db.return_value = mock_db_instance

    response = lambda_handler(mock_event, mock_context)

    assert response["statusCode"] == 200
    assert response["body"] == "file downloaded successfully"