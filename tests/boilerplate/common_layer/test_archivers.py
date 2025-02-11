"""
Unit tests for the archivers module.
"""

from datetime import datetime, timezone
from typing import NoReturn
from zipfile import ZipFile

import pytest
import requests
import requests.exceptions as req_exc
from pytest_mock import MockerFixture
from pytest import MonkeyPatch
from common_layer.database.client import SqlDB
from common_layer.database.models import AvlCavlDataArchive
from common_layer.archiver import (
    ArchiveDetails,
    ArchivingError,
    archive_data,
    get_content,
    upload_to_s3,
    upsert_cavl_table,
    zip_content,
    process_archive,
)


class MockResponse:
    """
    Mock response object for testing.
    """

    def __init__(self, content, status_code=200, raise_for_status_exception=None):
        """Initialize the response object."""
        self.content = content
        self.status_code = status_code
        self._raise_for_status_exception = raise_for_status_exception

    def raise_for_status(self) -> None:
        """Raise an exception for testing."""
        if self._raise_for_status_exception:
            raise self._raise_for_status_exception


def get_success(
    url: str, timeout: int
) -> MockResponse:  # pylint: disable=unused-argument
    """Get response for testing."""
    return MockResponse(b"dummy data", status_code=200)


def get_timeout(url: str, timeout: int) -> NoReturn:
    """Timeout exception for testing."""
    raise req_exc.Timeout("timeout occurred")


def get_conn_error(url: str, timeout: int) -> NoReturn:
    """Get connection error exception for testing."""
    raise req_exc.ConnectionError("connection error")


def get_http_error(
    url: str, timeout: int
) -> MockResponse:  # pylint: disable=unused-argument
    """Get HTTP error exception for testing."""
    response = MockResponse(
        b"error",
        status_code=404,
        raise_for_status_exception=req_exc.HTTPError("404 Not Found"),
    )
    return response


def get_request_exception(url: str, timeout: int) -> NoReturn:
    """Get request exception for testing."""
    raise req_exc.RequestException("generic request error")


def test_get_content_success(monkeypatch) -> None:
    """Test get content success."""
    monkeypatch.setattr(requests, "get", get_success)
    content = get_content("http://example.com")
    assert content == b"dummy data"


def test_get_content_timeout(monkeypatch: MonkeyPatch) -> None:
    """Test get content timeout."""
    monkeypatch.setattr(requests, "get", get_timeout)
    with pytest.raises(RuntimeError, match="timed out"):
        get_content("http://example.com")


def test_get_content_conn_error(monkeypatch: MonkeyPatch) -> None:
    """Test get content connection error."""
    monkeypatch.setattr(requests, "get", get_conn_error)
    with pytest.raises(RuntimeError, match="Network error"):
        get_content("http://example.com")


def test_get_content_http_error(monkeypatch: MonkeyPatch) -> None:
    """Test get content HTTP error."""
    monkeypatch.setattr(requests, "get", get_http_error)
    with pytest.raises(RuntimeError, match="HTTP error"):
        get_content("http://example.com")


def test_get_content_request_exception(monkeypatch: MonkeyPatch) -> None:
    """Test get content request exception."""
    monkeypatch.setattr(requests, "get", get_request_exception)
    with pytest.raises(RuntimeError, match="Unable to retrieve data"):
        get_content("http://example.com")


def test_zip_content(mocker: MockerFixture) -> None:
    """Test zip content."""
    mock_log = mocker.patch("common_layer.archiver.log")
    content = b"hello world"
    filename = "test.txt"

    zipped_bytes = zip_content(content, filename)
    mock_log.info.assert_called_once_with("Zipping content", filename=filename)

    zipped_bytes.seek(0)
    with ZipFile(zipped_bytes, "r") as zf:
        assert zf.namelist() == [filename]
        with zf.open(filename) as file_in_zip:
            assert file_in_zip.read() == content


def test_upload_to_s3(mocker: MockerFixture) -> None:
    """Test upload to s3."""
    mocker.patch("common_layer.archiver.BUCKET_NAME", "test-bucket")
    mock_s3_class = mocker.patch("common_layer.archiver.S3")

    filename = "test.txt"
    content = b"some test content"
    upload_to_s3(filename, content)
    mock_s3_class.assert_called_once_with("test-bucket")
    mock_s3_instance = mock_s3_class.return_value
    mock_s3_instance.put_object.assert_called_once_with(filename, content)


def test_upload_to_s3_no_bucket(mocker: MockerFixture) -> None:
    """Test upload to s3 without bucket."""
    mocker.patch("common_layer.archiver.BUCKET_NAME", "")
    mock_s3_class = mocker.patch("common_layer.archiver.S3")
    with pytest.raises(ValueError, match="S3 bucket not defined"):
        upload_to_s3("test.zip", b"content")
    mock_s3_class.assert_not_called()


def test_archive_data_success(monkeypatch: MonkeyPatch) -> None:
    """Test archive data success."""

    def _get_content(url):  # pylint: disable=unused-argument
        return b"fake content"

    fake_upload_calls = []

    def _upload_to_s3(filename, content):
        fake_upload_calls.append((filename, content))

    monkeypatch.setattr("common_layer.archiver.get_content", _get_content)
    monkeypatch.setattr("common_layer.archiver.upload_to_s3", _upload_to_s3)

    archive_details = ArchiveDetails(
        url="http://example.com",
        data_format="json",
        file_extension=".json",
        s3_file_prefix="data",
        local_file_prefix="local_data",
    )

    s3_filename, current_time = archive_data(archive_details)
    assert len(fake_upload_calls) == 1
    uploaded_filename, __ = fake_upload_calls[0]
    assert s3_filename == uploaded_filename
    assert s3_filename.startswith("data_")
    assert s3_filename.endswith(".zip")
    assert isinstance(current_time, datetime)


def test_archive_data_failure(monkeypatch: MonkeyPatch) -> None:
    """Test archive data failure."""

    def _get_content_failure(url):
        raise ValueError("failure")

    monkeypatch.setattr("common_layer.archiver.get_content", _get_content_failure)

    archive_details = ArchiveDetails(
        url="http://example.com",
        data_format="json",
        file_extension=".json",
        s3_file_prefix="data",
        local_file_prefix="local_data",
    )
    with pytest.raises(ArchivingError, match="Unable archive the date"):
        archive_data(archive_details)


def test_process_archive(mocker: MockerFixture) -> None:
    """Test process archive."""
    fake_file_name = "data_2025-02-11_123456.zip"
    fake_time = datetime(2025, 2, 11, 12, 34, 56, tzinfo=timezone.utc)

    mocker.patch(
        "common_layer.archiver.archive_data", return_value=(fake_file_name, fake_time)
    )
    mock_upsert = mocker.patch("common_layer.archiver.upsert_cavl_table")
    db_mock = mocker.create_autospec(SqlDB, instance=True)

    archive_details = ArchiveDetails(
        url="http://example.com",
        data_format="csv",
        file_extension=".csv",
        s3_file_prefix="data",
        local_file_prefix="local_data",
    )

    result = process_archive(db_mock, archive_details)
    assert result == fake_file_name

    mock_upsert.assert_called_once()
    call_args = mock_upsert.call_args[0]
    db_arg, data_format_arg, file_name_arg, current_time_arg = call_args

    assert db_arg is db_mock
    assert data_format_arg == "csv"
    assert file_name_arg == fake_file_name
    assert current_time_arg == fake_time


def test_upsert_cavl_table_insert(mocker: MockerFixture) -> None:
    """
    Test that a new record is inserted when no existing archive is found.
    """
    mock_repo_class = mocker.patch("common_layer.archiver.AvlCavlDataArchiveRepo")
    mock_repo_instance = mock_repo_class.return_value

    mock_repo_instance.get_by_data_format.return_value = None
    db = mocker.MagicMock(spec=SqlDB)

    data_format = "SIRIVM"
    file_name = "some_file.xml"
    current_time = datetime(2025, 1, 1, 10, 0, 0)

    upsert_cavl_table(db, data_format, file_name, current_time)
    mock_repo_instance.get_by_data_format.assert_called_once_with(data_format)
    mock_repo_instance.insert.assert_called_once()
    inserted_arg = mock_repo_instance.insert.call_args[0][0]

    assert inserted_arg.data_format == data_format
    assert inserted_arg.data == file_name
    assert inserted_arg.last_updated == current_time

    mock_repo_instance.update.assert_not_called()


def test_upsert_cavl_table_update(mocker: MockerFixture) -> None:
    """
    Test that an existing archive is updated when get_by_data_format returns a record.
    """
    mock_repo_class = mocker.patch("common_layer.archiver.AvlCavlDataArchiveRepo")
    mock_repo_instance = mock_repo_class.return_value

    existing_archive = AvlCavlDataArchive(data="SIRIVM", data_format="old_file.xml")
    existing_archive.last_updated = datetime(2024, 12, 31, 23, 0, 0)
    mock_repo_instance.get_by_data_format.return_value = existing_archive

    db = mocker.MagicMock(spec=SqlDB)

    data_format = "SIRIVM"
    file_name = "new_file.xml"
    current_time = datetime(2025, 1, 1, 10, 0, 0)
    upsert_cavl_table(db, data_format, file_name, current_time)

    mock_repo_instance.get_by_data_format.assert_called_once_with(data_format)
    mock_repo_instance.update.assert_called_once_with(existing_archive)
    mock_repo_instance.insert.assert_not_called()

    assert existing_archive.data == file_name
