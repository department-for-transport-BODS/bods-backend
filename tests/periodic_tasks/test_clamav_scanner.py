import io
import unittest
from unittest.mock import patch, MagicMock
from src.periodic_tasks.clamav_scanner import (
    FileScanner,
    lambda_handler,
    AntiVirusError,
    SuspiciousFile,
    ClamConnectionError)


class TestClamAVScanner(unittest.TestCase):
    def setUp(self):
        self.host_port = ('abc', 9876)
        self.file_name = 'bodds.zip'  # noqa
        self.file_io = io.BytesIO(b"testing scanner")
        self.file_io.name = self.file_name

    @patch("src.periodic_tasks.clamav_scanner.ClamdNetworkSocket")
    def test_file_scanner_scan(self, mock_clamd_network_sockets):
        mock_av_instance = mock_clamd_network_sockets.return_value
        mock_av_instance.instream.return_value = {"stream": ("virusname", "status")}

        file_scanner = FileScanner(*self.host_port)
        file_scanner.scan(self.file_io)

        mock_av_instance.instream.assert_called_once_with(self.file_io)

    @patch("src.periodic_tasks.clamav_scanner.ClamdNetworkSocket")
    def test_file_scanner_scan_exception(self, mock_clamd_network_sockets):
        # Mock the ClamdNetworkSocket
        mock_av_instance = mock_clamd_network_sockets.return_value
        exception_msg = "Exception raised when scanning file"

        for _exception in (ClamConnectionError, AntiVirusError, SuspiciousFile):
            mock_av_instance.instream.side_effect = _exception(exception_msg)
            file_scanner = FileScanner(*self.host_port)
            with self.assertRaises(_exception) as context:
                file_scanner.scan(self.file_io)
            self.assertEqual(str(context.exception), exception_msg)

        self.assertEqual(mock_av_instance.instream.call_count, 3)

    @patch('src.periodic_tasks.clamav_scanner.S3')
    @patch('src.periodic_tasks.clamav_scanner.FileScanner')
    @patch.dict('os.environ', {'CLAMAV_HOST': 'abc', 'CLAMAV_PORT': '1234'})
    def test_lambda_handler_success(self, mock_file_scanner, mock_s3):
        # Mock instances for FileScanner and S3
        mock_file_scanner_instance = mock_file_scanner.return_value
        mock_s3_instance = mock_s3.return_value

        # Set up successful mock behavior for FileScanner and S3 methods
        mock_file_scanner_instance.scan = MagicMock()
        mock_s3_instance.get_object.return_value = self.file_io

        # Define a sample event
        event = {
            "Records": [
                {
                    "eventVersion": "2.2",
                    "eventSource": "aws:s3",
                    "awsRegion": "us-west-2",
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "bucket": {
                            "name": "bodds-dev",
                        },
                        "object": {"key": self.file_name}
                    }
                }
            ]
        }

        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = event["Records"][0]["s3"]["object"]["key"]

        # Invoke lambda_handler
        response = lambda_handler(event, None)

        # Assert that FileScanner and S3 methods were called
        mock_file_scanner_instance.scan.assert_called_once_with(self.file_io)
        mock_s3_instance.get_object.assert_called_once_with(file_path=key)

        # Verify the response is successful
        self.assertEqual(response["statusCode"], 200)

    @patch('src.periodic_tasks.clamav_scanner.S3')
    @patch('src.periodic_tasks.clamav_scanner.FileScanner')
    @patch.dict('os.environ', {'CLAMAV_HOST': 'abc', 'CLAMAV_PORT': '1234'})
    def test_lambda_handler_exceptions(self, mock_file_scanner, mock_s3):
        # Mock instances for FileScanner and S3
        mock_file_scanner_instance = mock_file_scanner.return_value
        mock_s3_instance = mock_s3.return_value

        # Set up successful mock behavior for FileScanner and S3 methods
        mock_s3_instance.get_object.return_value = self.file_io

        # Define a sample event
        event = {
            "Records": [
                {
                    "eventVersion": "2.2",
                    "eventSource": "aws:s3",
                    "awsRegion": "us-west-2",
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "bucket": {
                            "name": "bodds-dev",
                        },
                        "object": {"key": self.file_name}
                    }
                }
            ]
        }

        msg = "Exception raised when scanning file"
        for _exception in (Exception, AntiVirusError):
            mock_file_scanner_instance.scan.side_effect = _exception(msg)
            with self.assertRaises(_exception) as context:
                # Invoke lambda_handler
                response = lambda_handler(event, None)

                self.assertEqual(str(context.exception), msg)


if __name__ == '__main__':
    unittest.main()