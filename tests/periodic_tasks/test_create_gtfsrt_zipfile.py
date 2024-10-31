import unittest
from unittest.mock import patch
from periodic_tasks.create_gtfsrt_zip import lambda_handler

MODULE_PATH = "periodic_tasks.create_gtfsrt_zip"


class TestGtfsrtZipfile(unittest.TestCase):

    @patch(f"{MODULE_PATH}.GTFSRTArchiver")
    def test_archiver_called(self, MockArchiver):
        mock_instance = MockArchiver.return_value
        lambda_handler({}, "")
        mock_instance.archive.assert_called_once()

    @patch(f"{MODULE_PATH}.logger")
    @patch(f"{MODULE_PATH}.GTFSRTArchiver")
    def test_general_exception(self, mock_archiver, mock_logger):
        mock_instance = mock_archiver.return_value
        mock_instance.url = "http://fakeurl.com"
        mock_instance.archive.side_effect = Exception("General error")

        lambda_handler({}, "")
        mock_logger.error.assert_called_once_with(
            "GTFSRT zip task failed due to General error"
        )
