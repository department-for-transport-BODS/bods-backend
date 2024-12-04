from io import BytesIO
import unittest
from unittest.mock import patch, MagicMock
from clamd import BufferTooLongError, ConnectionError
from timetables_etl.clamav_scanner import (
    FileScanner,
    lambda_handler,
    AntiVirusError,
    SuspiciousFile,
    ClamConnectionError)
from tests.mock_db import MockedDB

TEST_ENV_VAR = {"PROJECT_ENV": "dev",
                "CLAMAV_HOST": "abc",
                "CLAMAV_PORT": "1234",
                "POSTGRES_HOST": "sample_host",
                "POSTGRES_PORT": "1234",
                "POSTGRES_USER": "sample_user",
                "POSTGRES_PASSWORD": "<PASSWORD>"
                }


class TestClamAVScanner(unittest.TestCase):
    @patch("timetables_etl.clamav_scanner.ClamdNetworkSocket")
    def setUp(self, mock_clamd):
        self.file_name = 'bodds.zip' # noqa
        self.mock_clamd_instance = mock_clamd.return_value
        self.file_scanner = FileScanner("http://clamavhost.example", 9876)

    def test_scan_file_success(self):
        self.mock_clamd_instance.instream.return_value = {"stream": ("OK", None)}
        with BytesIO(b"sample data") as f:
            f.name = self.file_name
            result = self.file_scanner.scan(f)

        self.assertIsNone(result)

    def test_scan_file_virus_found(self):
        buf = {"stream": ("FOUND", "Virus detected")}
        self.mock_clamd_instance.instream.return_value = buf
        with self.assertRaises(SuspiciousFile) as context:
            with BytesIO(b"infected data") as f:
                f.name = self.file_name
                self.file_scanner.scan(f)

        self.assertIn("Virus detected", str(context.exception))

    def test_scan_file_error(self):
        buf = {"stream": ("ERROR", "Scan error")}
        self.mock_clamd_instance.instream.return_value = buf
        with self.assertRaises(AntiVirusError) as context:
            with BytesIO(b"corrupt data") as f:
                f.name = self.file_name
                self.file_scanner.scan(f)

        self.assertIn(self.file_name, str(context.exception))

    def test_buffer_too_long_error(self):
        self.mock_clamd_instance.instream.side_effect = BufferTooLongError
        with self.assertRaises(AntiVirusError) as context:
            with BytesIO(b"large file data") as f:
                f.name = self.file_name
                self.file_scanner.scan(f)

        self.assertIn(self.file_name, str(context.exception))

    def test_connection_error(self):
        self.mock_clamd_instance.instream.side_effect = ConnectionError
        with self.assertRaises(ClamConnectionError) as context:
            with BytesIO(b"network error data") as f:
                f.name = self.file_name
                self.file_scanner.scan(f)

        self.assertIn(self.file_name, str(context.exception))

    @patch("timetables_etl.clamav_scanner.S3")
    @patch("timetables_etl.clamav_scanner.FileScanner")
    @patch("timetables_etl.clamav_scanner.unzip")
    @patch("db.file_processing_result.BodsDB")
    @patch("db.file_processing_result.get_revision")
    @patch("timetables_etl.clamav_scanner.update_file_hash")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_lambda_handler_success(self,
                                    mock_update_file_hash,
                                    mock_get_revision,
                                    mock_db,
                                    mock_unzip,
                                    mock_file_scanner,
                                    mock_s3):
        # Mock get revision
        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        # Mock S3 behavior
        mock_s3_instance = mock_s3.return_value
        mock_file_object = MagicMock()
        mock_s3_instance.get_object.return_value = mock_file_object

        mock_unzip.return_value = MagicMock()

        # Mock FileScanner behavior
        mock_scanner_instance = mock_file_scanner.return_value
        mock_scanner_instance.clamav.ping.return_value = True

        # Define a sample Lambda event
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": self.file_name,
            "DatasetRevisionId": 123,
            "DatasetType": "timetables"
        }

        # Mock write_processing_step
        buf_ = "db.file_processing_result.write_processing_step"

        with patch(buf_) as mock_step:
            mock_step.return_value = MagicMock(id=1)
            mock_db.return_value = MockedDB()

            # Execute lambda_handler
            result = lambda_handler(event, None)

            # Assert success response
            self.assertEqual(result["statusCode"], 200)
            self.assertIn("Successfully scanned", result["body"]["message"])

            # Verify S3 and FileScanner were called correctly
            mock_s3.assert_called_once_with(bucket_name="test-bucket")
            self.assertEqual(mock_s3_instance.get_object.call_count, 2)
            mock_scanner_instance.clamav.ping.assert_called_once()
            mock_scanner_instance.scan.assert_called_once_with(mock_file_object)

    @patch("timetables_etl.clamav_scanner.S3")
    @patch("timetables_etl.clamav_scanner.FileScanner")
    @patch('db.file_processing_result.BodsDB')
    @patch("db.file_processing_result.get_revision")
    @patch("timetables_etl.clamav_scanner.update_file_hash")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_lambda_handler_clamav_unreachable(self,
                                               mock_update_file_hash,
                                               mock_get_revision,
                                               mock_db,
                                               mock_file_scanner,
                                               mock_s3):
        # Mock get revision
        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        # Mock S3 behavior
        mock_s3_instance = mock_s3.return_value
        mock_file_object = MagicMock()
        mock_s3_instance.get_object.return_value = mock_file_object

        # Mock FileScanner to simulate ClamAV being unreachable
        mock_scanner_instance = mock_file_scanner.return_value
        mock_scanner_instance.clamav.ping.return_value = False

        # Define a sample Lambda event
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": self.file_name,
            "DatasetRevisionId": 123,
            "DatasetType": "timetables"
        }

        # Mock write_processing_step
        buf_ = "db.file_processing_result.write_processing_step"
        with patch(buf_) as mock_step:
            mock_step.return_value = MagicMock(id=1)
            mock_db.return_value = MockedDB()
            # Mock write_error_to_db
            buf_ = "db.file_processing_result.write_error_to_db"
            with patch(buf_) as mock_write_db:
                mock_write_db.return_value = "Transaction committed"
                # Assert exception due to ClamAV unreachability
                with self.assertRaises(ClamConnectionError) as context:
                    lambda_handler(event, None)

                # Verify the exception message
                self.assertIn("ClamAV is not running or accessible.",
                              str(context.exception))

    @patch("timetables_etl.clamav_scanner.S3")
    @patch("timetables_etl.clamav_scanner.FileScanner")
    @patch('db.file_processing_result.BodsDB')
    @patch("db.file_processing_result.get_revision")
    @patch("timetables_etl.clamav_scanner.update_file_hash")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_lambda_handler_scan_error(self,
                                       mock_update_file_hash,
                                       mock_get_revision,
                                       mock_db,
                                       mock_file_scanner,
                                       mock_s3):
        # Mock get revision
        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        # Mock S3 behavior
        mock_s3_instance = mock_s3.return_value
        mock_file_object = MagicMock()
        mock_s3_instance.get_object.return_value = mock_file_object

        # Simulate error during scan
        mock_scanner_instance = mock_file_scanner.return_value
        mock_scanner_instance.clamav.ping.return_value = True
        mock_scanner_instance.scan.side_effect = AntiVirusError("Scan failed")

        # Define a sample Lambda event
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": self.file_name,
            "DatasetRevisionId": 123,
            "DatasetType": "timetables"
        }
        # Mock write_processing_step
        buf_ = "db.file_processing_result.write_processing_step"
        with patch(buf_) as mock_step:
            mock_step.return_value = MagicMock(id=1)
            mock_db.return_value = MockedDB()
            # Mock write_error_to_db
            buf_ = "db.file_processing_result.write_error_to_db"
            with patch(buf_) as mock_write_db:
                mock_write_db.return_value = "Transaction committed"
                # Assert exception due to scan error
                with self.assertRaises(Exception) as context:
                    lambda_handler(event, None)

                # Verify the exception message
                self.assertIn("Scan failed", str(context.exception))


if __name__ == '__main__':
    unittest.main()