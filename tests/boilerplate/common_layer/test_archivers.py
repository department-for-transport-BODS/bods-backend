"""
Unit tests for the archivers module.
"""

import io
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

import pytest
from common_layer.archiver import ConsumerAPIArchiver, SiriVMArchiver, upsert_cavl_table
from common_layer.database.client import SqlDB
from common_layer.database.models import AvlCavlDataArchive
from common_layer.database.repos import AvlCavlDataArchiveRepo
from common_layer.s3 import S3

# Sample test URL and test content
TEST_URL = "https://example.com/api/data"
TEST_RESPONSE_CONTENT = b"<xml>Sample Data</xml>"
TEST_DATA_FORMAT = "SIRIVM"
TEST_FILE_NAME = "sirivm_2025-02-01_120000.zip"


@pytest.fixture(name="mock_db")
def mock_db_fixture():
    """Fixture to mock the database"""
    return MagicMock(spec=SqlDB)


@pytest.fixture(name="mock_s3")
def mock_s3_fixture():
    """Fixture to mock S3"""
    with patch.object(S3, "put_object") as mock_s3:
        yield mock_s3


@pytest.fixture(name="mock_avl_repo")
def mock_avl_repo_fixture():
    """Fixture to mock AvlCavlDataArchiveRepo"""
    with patch.object(
        AvlCavlDataArchiveRepo, "get_by_data_format", return_value=None
    ), patch.object(AvlCavlDataArchiveRepo, "insert") as mock_insert, patch.object(
        AvlCavlDataArchiveRepo, "update"
    ) as mock_update, patch.object(
        AvlCavlDataArchiveRepo, "get_by_data_format", return_value=None
    ) as mock_get:
        yield mock_insert, mock_update, mock_get


@pytest.fixture(name="mock_requests_get")
def mock_requests_get_fixture():
    """Fixture to mock requests.get"""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.content = TEST_RESPONSE_CONTENT
        mock_response.elapsed.total_seconds.return_value = 1.23
        mock_get.return_value = mock_response
        yield mock_get


def test_upsert_cavl_table_insert_new_record(mock_db, mock_avl_repo):
    """Test inserting a new record when no existing record is found"""
    mock_insert, mock_update, mock_get = mock_avl_repo

    # Mock `get_by_data_format` to return None (no existing record)
    mock_get.return_value = None

    # Run function
    upsert_cavl_table(mock_db, TEST_DATA_FORMAT, TEST_FILE_NAME)

    # Assertions
    mock_insert.assert_called_once()
    inserted_record = mock_insert.call_args[0][0]
    assert inserted_record.data_format == TEST_DATA_FORMAT
    assert inserted_record.data == TEST_FILE_NAME
    mock_update.assert_not_called()


def test_upsert_cavl_table_update_existing_record(mock_db, mock_avl_repo):
    """Test updating an existing record when a record is found"""
    mock_insert, mock_update, mock_get = mock_avl_repo

    # Mock existing record
    existing_record = MagicMock(spec=AvlCavlDataArchive)
    existing_record.data_format = TEST_DATA_FORMAT
    existing_record.data = "old_file.zip"
    existing_record.last_updated = None

    # Mock `get_by_data_format` to return an existing record
    mock_get.return_value = existing_record

    # Run function
    upsert_cavl_table(mock_db, TEST_DATA_FORMAT, TEST_FILE_NAME)

    # Assertions
    mock_update.assert_called_once_with(existing_record)
    assert existing_record.last_updated is not None
    assert isinstance(existing_record.last_updated, datetime)
    mock_insert.assert_not_called()


def test_get_content(mock_requests_get):
    """Test `_get_content()` method fetches data correctly"""
    archiver = ConsumerAPIArchiver(TEST_URL)
    content = archiver._get_content()  # pylint: disable=protected-access

    # Assertions
    assert content == TEST_RESPONSE_CONTENT
    mock_requests_get.assert_called_once_with(TEST_URL)
    assert isinstance(
        archiver._access_time, datetime
    )  # pylint: disable=protected-access


def test_get_file():
    """Test `get_file()` method creates a valid ZIP file"""
    archiver = ConsumerAPIArchiver(TEST_URL)
    zip_bytes = archiver.get_file(TEST_RESPONSE_CONTENT)

    # Ensure it's a valid ZIP file
    zip_bytes.seek(0)
    with ZipFile(zip_bytes, "r") as zip_file:
        assert (
            archiver.content_filename in zip_file.namelist()
        )  # Ensure filename exists


def test_save_to_database(
    mock_db, mock_s3, mock_avl_repo
):  # pylint: disable=unused-argument
    """Test `save_to_database()` saves correctly"""
    archiver = ConsumerAPIArchiver(TEST_URL)

    # Mock _get_content() to fetch valid content
    with patch.object(archiver, "_get_content", return_value=b"<xml>Data</xml>"):
        # pylint: disable=protected-access
        archiver._content = archiver._get_content()
        archiver._access_time = datetime.now(timezone.utc)

        # Mock ZIP file creation
        zip_file = io.BytesIO()
        zip_file.write(b"Test Data")
        zip_file.seek(0)

        archiver.save_to_database(zip_file)

        # Assertions
        mock_s3.assert_called_once()
        mock_avl_repo[0].assert_called_once()


def test_sirivm_archiver(
    mock_requests_get, mock_db, mock_s3, mock_avl_repo
):  # pylint: disable=unused-argument
    """Test `SiriVMArchiver` class functionality"""
    archiver = SiriVMArchiver(TEST_URL)

    # Mock `_get_content()` to fetch valid content
    with patch.object(archiver, "_get_content", return_value=b"<xml>Data</xml>"):
        # pylint: disable=protected-access
        archiver._content = archiver._get_content()  # Initialize content
        archiver._access_time = datetime(2025, 2, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Run archive process
        archiver.archive()

        # Assertions
        mock_s3.assert_called_once()
        mock_avl_repo[0].assert_called_once()
