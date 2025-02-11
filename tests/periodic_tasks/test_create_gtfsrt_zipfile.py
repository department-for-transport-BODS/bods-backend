"""
Unit test for create_gtfsrt_zipfile lambda handler.
"""

import unittest
from unittest.mock import MagicMock, patch

from periodic_tasks.create_gtfsrt_zip import lambda_handler

LAMBDA_PATH = "periodic_tasks.create_gtfsrt_zip"


class TestLambdaHandler(unittest.TestCase):
    """Unit test for create_gtfsrt_zipfile lambda handler."""

    @patch(f"{LAMBDA_PATH}.archive_data")
    @patch(f"{LAMBDA_PATH}.environ.get")
    @patch(f"{LAMBDA_PATH}.configure_logging")
    def test_lambda_handler_success(
        self, mock_configure_logging, mock_environ_get, mock_archive_data
    ):
        """Testing lambda_handler success."""
        mock_environ_get.side_effect = lambda key, default=None: {
            "AWS_SIRIVM_STORAGE_BUCKET_NAME": "test-bucket",
            "GTFS_API_ACTIVE": "True",
            "GTFS_API_BASE_URL": "http://example.com",
            "CAVL_CONSUMER_URL": "http://consumer.com",
        }.get(key, default)

        event = {"key": "value"}
        context = MagicMock()
        response = lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Successfully archived gtfsrt data", response["body"])
        mock_archive_data.assert_called_once()
        mock_configure_logging.assert_called_once_with(event, context)

    @patch(f"{LAMBDA_PATH}.archive_data", side_effect=Exception("Archiving error"))
    @patch(f"{LAMBDA_PATH}.environ.get")
    @patch(f"{LAMBDA_PATH}.configure_logging")
    def test_lambda_handler_failure(
        self, mock_configure_logging, mock_environ_get, mock_archive_data
    ):
        """Testing lambda_handler failure."""
        mock_environ_get.side_effect = lambda key, default=None: {
            "AWS_SIRIVM_STORAGE_BUCKET_NAME": "test-bucket",
            "GTFS_API_ACTIVE": "True",
            "GTFS_API_BASE_URL": "http://example.com",
            "CAVL_CONSUMER_URL": "http://consumer.com",
        }.get(key, default)

        event = {"key": "value"}
        context = MagicMock()

        with self.assertRaises(Exception) as exc:
            lambda_handler(event, context)

        self.assertIn("Archiving error", str(exc.exception))
        mock_archive_data.assert_called_once()
        mock_configure_logging.assert_called_once_with(event, context)
