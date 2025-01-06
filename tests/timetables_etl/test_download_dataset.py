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
    SqlDB,
    UnknownFileType,
    bytes_are_zip_file,
    download_and_upload_dataset,
    download_data_from_remote_url,
    get_filetype_from_response,
    lambda_handler,
    update_dataset_revision,
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


def create_valid_zip():
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("test.txt", "This is a test file.")
    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (lambda: create_valid_zip(), True),
        (b"not a zip file", False),
        (b"", False),
        (b"<?xml version='1.0' encoding='UTF-8'?>", False),
    ],
    ids=["Valid ZIP file", "Invalid ZIP file", "Empty content", "XML content"],
)
def test_bytes_are_zip_file(test_input, expected):
    """
    Test the `bytes_are_zip_file` function with various input types.
    """
    if callable(test_input):  # If the input is a callable (for valid zip content)
        test_input = test_input()

    assert bytes_are_zip_file(test_input) is expected


@pytest.mark.parametrize(
    "content_type, content, expected_filetype, test_id",
    [
        ("application/zip", b"\x50\x4b\x03\x04", "zip", "ZIP file by Content-Type"),
        (
            "application/xml",
            b"<?xml version='1.0' encoding='UTF-8'?>",
            "xml",
            "XML file by Content-Type",
        ),
        ("application/json", b"{}", None, "Unknown file by Content-Type"),
        ("application/json", create_valid_zip(), "zip", "ZIP file by Content"),
    ],
    ids=[
        "ZIP file by Content-Type",
        "XML file by Content-Type",
        "Unknown file by Content-Type",
        "ZIP file by Content",
    ],
)
def test_get_filetype_from_response(content_type, content, expected_filetype, test_id):
    """
    Test the `get_filetype_from_response` function with various file responses.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": content_type}
    mock_response.content = content

    result = get_filetype_from_response(mock_response)
    assert result == expected_filetype, f"Failed for test case: {test_id}"


@pytest.mark.parametrize(
    "content_type, content, expected_filetype, should_raise, test_id",
    [
        ("application/zip", b"\x50\x4b\x03\x04", "zip", False, "ZIP file response"),
        (
            "application/xml",
            b"<?xml version='1.0' encoding='UTF-8'?>",
            "xml",
            False,
            "XML file response",
        ),
        ("text/plain", b"Invalid content", None, True, "Unknown file response"),
    ],
    ids=["ZIP file response", "XML file response", "Unknown file response"],
)
def test_get(
    mock_data_downloader,
    content_type,
    content,
    expected_filetype,
    should_raise,
    test_id,
):
    """
    Test the `get` method of the `mock_data_downloader` to handle various file responses.
    """
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": content_type}
    mock_response.content = content
    mock_data_downloader._make_request = MagicMock(return_value=mock_response)

    if should_raise:
        with pytest.raises(UnknownFileType):
            mock_data_downloader.get()
    else:
        result = mock_data_downloader.get()
        assert result.filetype == expected_filetype
        assert result.content == content, f"Failed for test case: {test_id}"


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


@pytest.mark.parametrize(
    "event, expected_status_code, expected_body, should_raise, test_id",
    [
        (
            # Test case 1: No URL link
            {
                "Bucket": "my-bucket",
                "ObjectKey": "file.zip",
                "DatasetRevisionId": 1,
                "DatasetEtlTaskResultId": "1234",
            },
            200,
            "url link is not specified, nothing to download",
            False,
            "No URL Link",
        ),
        (
            # Test case 2: Invalid URL link (should raise ValueError)
            {
                "Bucket": "my-bucket",
                "ObjectKey": "file.zip",
                "DatasetRevisionId": 1,
                "DatasetEtlTaskResultId": "1234",
                "URLLink": "//fakeurl.com/file.zip",
            },
            None,
            None,
            True,
            "Invalid URL Link",
        ),
        (
            # Test case 3: Valid URL link
            {
                "Bucket": "my-bucket",
                "ObjectKey": "file.zip",
                "URLLink": "https://fakeurl.com/file.zip",
                "DatasetRevisionId": 1,
                "DatasetEtlTaskResultId": "1234",
            },
            200,
            "file downloaded successfully",
            False,
            "Valid URL Link",
        ),
    ],
    ids=["No URL Link", "Invalid URL Link", "Valid URL Link"],
)
@patch("common_layer.db.file_processing_result.SqlDB")
@patch("timetables_etl.download_dataset.download_and_upload_dataset")
@patch.dict("os.environ", TEST_ENV_VAR)
def test_lambda_handler(
    mock_download_upload_dataset,
    mock_sqldb,
    event,
    expected_status_code,
    expected_body,
    should_raise,
    test_id,
):
    """
    Test the `lambda_handler` method with various event conditions.
    """
    mock_db_instance = MagicMock()
    mock_sqldb.get_db.return_value = mock_db_instance
    mock_response = {"statusCode": 200, "body": "file downloaded successfully"}
    mock_download_upload_dataset.return_value = mock_response
    mock_context = MagicMock()

    if should_raise:
        with pytest.raises(ValueError):
            lambda_handler(event, mock_context)
    else:
        response = lambda_handler(event, mock_context)
        assert response["statusCode"] == expected_status_code
        assert response["body"] == expected_body, f"Failed for {test_id}"


@patch("timetables_etl.download_dataset.S3")
@patch("common_layer.database.client.SqlDB")
@patch("timetables_etl.download_dataset.get_revision")
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
    mock_get_revision,
    mock_sqldb,
    mock_s3,
):
    """
    Test the `download_and_upload_dataset` method to download the file from url and update the db object
    """
    EXPECTED_RESPONSE = {"body": "file downloaded successfully", "statusCode": 200}
    mock_sqldb.return_value = MagicMock()
    mock_s3.return_value = MagicMock()
    mock_get_revision.return_value = MagicMock()
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


@pytest.mark.parametrize(
    "side_effect, expected_exception, mock_response, test_id",
    [
        (None, None, b"fake data", "Success Case"),
        (DownloadException("Download failed"), PipelineException, None, "Failure Case"),
    ],
    ids=["Success Case", "Failure Case"],
)
def test_download_data(
    mock_revision, side_effect, expected_exception, mock_response, test_id
):
    """
    Test the `download_data_from_remote_url` function for both success and failure cases.
    """
    # Mock the DataDownloader.get method to return a predefined response or raise an exception
    with patch.object(DataDownloader, "get", side_effect=side_effect) as mock_get:
        if expected_exception:
            # Test failure case where the exception is raised
            with pytest.raises(expected_exception, match="Download failed"):
                download_data_from_remote_url(mock_revision)
        else:
            # Test success case where the download is successful
            mock_get.return_value = MagicMock(content=mock_response)
            response = download_data_from_remote_url(mock_revision)
            assert response.content == mock_response
            mock_get.assert_called_once()


@pytest.mark.parametrize(
    "mock_revision_return, expected_upload_file, expected_update_called, test_id",
    [
        # Case 1: Revision exists
        (MagicMock(upload_file=None), "new_file.csv", True, "Revision Exists"),
        # Case 2: Revision does not exist
        (None, None, False, "Revision Not Found"),
    ],
    ids=["Revision Exists", "Revision Not Found"],
)
@patch("timetables_etl.download_dataset.log")
@patch("timetables_etl.download_dataset.OrganisationDatasetRevisionRepo")
def test_update_dataset_revision(
    mock_repo_class,
    mock_log,
    mock_revision_return,
    expected_upload_file,
    expected_update_called,
    test_id,
):
    """
    Test the `update_dataset_revision` method for different revision states.
    """
    mock_db = MagicMock(SqlDB)
    mock_revision_repo = MagicMock()
    mock_repo_class.return_value = mock_revision_repo
    mock_revision_repo.get_by_id.return_value = mock_revision_return

    revision_id = 1
    file_name = "new_file.csv"

    update_dataset_revision(revision_id, file_name, mock_db)
    mock_revision_repo.get_by_id.assert_called_once_with(revision_id)
    if expected_update_called:
        mock_revision_repo.update.assert_called_once_with(mock_revision_return)
        assert mock_revision_return.upload_file == expected_upload_file
    else:
        mock_revision_repo.update.assert_not_called()
