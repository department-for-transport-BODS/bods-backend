import unittest
from unittest.mock import patch
from periodic_tasks.create_sirivm_zip import lambda_handler

MODULE_PATH = "src.periodic_tasks.create_sirivm_zip"


class TestSIRIVMZipfile(unittest.TestCase):

    @patch(f"{MODULE_PATH}.SiriVMArchiver")
    def test_archiver_called(self, MockArchiver):
        mock_instance = MockArchiver.return_value
        lambda_handler({}, "")
        mock_instance.archive.assert_called_once()

    @patch(f"{MODULE_PATH}.logger")
    @patch(f"{MODULE_PATH}.SiriVMArchiver")
    def test_general_exception(self, mock_archiver, mock_logger):
        mock_instance = mock_archiver.return_value
        mock_instance.url = "http://fakeurl.com"
        mock_instance.archive.side_effect = Exception("General error")

        lambda_handler({}, "")
        mock_logger.error.assert_called_once_with(
            "SIRIVM zip task failed due to General error"
        )
