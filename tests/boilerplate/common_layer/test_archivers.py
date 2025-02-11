"""
Unit tests for the archivers module.
"""

import unittest
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch

from common_layer.archiver import (
    ArchiveDetails,
    ArchivingError,
    archive_data,
    get_content,
    upload_to_s3,
    upsert_cavl_table,
    zip_content,
)
from requests import exceptions


class TestArchiving(unittest.TestCase):
    """Test cases for archivers module."""

    @patch("common_layer.archiver.requests.get")
    def test_get_content_success(self, mock_get):
        """Test case for get_content success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"test data"
        mock_get.return_value = mock_response

        content = get_content("http://example.com")
        self.assertEqual(content, b"test data")
        mock_get.assert_called_once()

    @patch("common_layer.archiver.requests.get", side_effect=exceptions.Timeout)
    def test_get_content_timeout(self, mock_get):
        """Test case for get_content timeout."""
        with self.assertRaises(RuntimeError) as exc:
            get_content("http://example.com")
        self.assertIn("timed out", str(exc.exception))
        mock_get.assert_called_once()

    @patch("common_layer.archiver.requests.get", side_effect=exceptions.ConnectionError)
    def test_get_content_connection_error(self, mock_get):
        """Test case for get_content connection error."""
        with self.assertRaises(RuntimeError) as exc:
            get_content("http://example.com")
        self.assertIn("Network error", str(exc.exception))
        mock_get.assert_called_once()

    @patch("common_layer.archiver.requests.get")
    def test_get_content_http_error(self, mock_get):
        """Test case for get_content HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = exceptions.HTTPError(
            "Internal Server Error"
        )
        mock_get.return_value = mock_response

        with self.assertRaises(RuntimeError) as exc:
            get_content("http://example.com")
        self.assertIn("HTTP error 500", str(exc.exception))

    @patch(
        "common_layer.archiver.requests.get",
        side_effect=exceptions.RequestException("Unknown error"),
    )
    def test_get_content_request_exception(self, mock_get):
        """Test case for get_content request exception."""
        with self.assertRaises(RuntimeError) as exc:
            get_content("http://example.com")
        self.assertIn("Unable to retrieve data", str(exc.exception))
        mock_get.assert_called_once()

    def test_zip_content(self):
        """Test case for zip_content."""
        content = b"test data"
        filename = "test.xml"
        zipped_file = zip_content(content, filename)

        self.assertIsInstance(zipped_file, BytesIO)

    @patch("common_layer.archiver.S3")
    @patch("common_layer.archiver.environ.get", return_value="test-bucket")
    def test_upload_to_s3(self, _mock_env, mock_s3):
        """Test case for upload_to_s3."""
        mock_s3_instance = mock_s3.return_value
        upload_to_s3("test.zip", b"zip content")

        mock_s3_instance.put_object.assert_called_with("test.zip", b"zip content")

    @patch("common_layer.archiver.SqlDB")
    @patch("common_layer.archiver.AvlCavlDataArchiveRepo")
    def test_upsert_cavl_table_insert(self, mock_repo, mock_db):
        """Test case for upsert_cavl_table."""
        mock_repo_instance = mock_repo.return_value
        mock_repo_instance.get_by_data_format.return_value = None
        upsert_cavl_table(mock_db, "TEST_FORMAT", "test.zip", datetime(2020, 1, 1))

        mock_repo_instance.insert.assert_called()

    @patch("common_layer.archiver.SqlDB")
    @patch("common_layer.archiver.AvlCavlDataArchiveRepo")
    def test_upsert_cavl_table_update(self, mock_repo, mock_db):
        """Test case for upsert_cavl_table."""
        mock_repo_instance = mock_repo.return_value
        archive_mock = MagicMock()
        mock_repo_instance.get_by_data_format.return_value = archive_mock
        upsert_cavl_table(mock_db, "TEST_FORMAT", "test.zip", datetime(2020, 1, 1))

        self.assertEqual(archive_mock.data, "test.zip")
        mock_repo_instance.update.assert_called()

    @patch("common_layer.archiver.get_content", return_value=b"test data")
    @patch("common_layer.archiver.zip_content", return_value=BytesIO(b"zipped data"))
    @patch("common_layer.archiver.upload_to_s3")
    @patch("common_layer.archiver.upsert_cavl_table")
    def test_archive_data(self, mock_upsert, mock_upload, mock_zip, mock_get):
        """Test case for archive_data."""
        archive_details = ArchiveDetails(
            url="http://example.com",
            data_format="TEST_FORMAT",
            file_extension=".xml",
            s3_file_prefix="test_prefix",
            local_file_prefix="test_local",
        )

        archive_data(archive_details)

        mock_get.assert_called()
        mock_zip.assert_called()
        mock_upload.assert_called()
        mock_upsert.assert_called()

    @patch("common_layer.archiver.get_content", side_effect=Exception("Failed"))
    def test_archive_data_failure(self, mock_get):
        """Test case for archive_data."""
        archive_details = ArchiveDetails(
            url="http://example.com",
            data_format="TEST_FORMAT",
            file_extension=".xml",
            s3_file_prefix="test_prefix",
            local_file_prefix="test_local",
        )

        with self.assertRaises(ArchivingError):
            archive_data(archive_details)
        mock_get.assert_called_once()
