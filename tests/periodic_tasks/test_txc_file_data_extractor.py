from io import BytesIO
import unittest
from unittest.mock import patch, MagicMock
from tests.mock_db import MockedDB
from periodic_tasks.txc_file_data_extractor import lambda_handler


class TestLambdaHandler(unittest.TestCase):
    @patch("periodic_tasks.txc_file_data_extractor.logger")
    @patch("periodic_tasks.txc_file_data_extractor.txc_file_attributes_to_db")
    @patch("periodic_tasks.txc_file_data_extractor.TransXChangeDatasetParser")
    @patch("periodic_tasks.txc_file_data_extractor.S3")
    def test_lambda_handler_success(
        self, mock_s3, mock_parser, mock_txc_file_attributes_to_db, mock_logger
    ):
        # Set up mock event data
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "4567/test-key", "revision_id": 123},
                    }
                }
            ]
        }

        # Mock S3 handler's get_object method
        mock_s3_instance = mock_s3.return_value
        mock_s3_instance.get_object.return_value = BytesIO(b"mock XML content")

        # Mock the TransXChangeDatasetParser to return fake documents
        mock_parser_instance = mock_parser.return_value
        mock_doc = MagicMock()
        mock_parser_instance.get_documents.return_value = [mock_doc]

        # Mock TXCFile to simulate parsed data
        mock_txc_file = MagicMock()
        buf = "periodic_tasks.txc_file_data_extractor.TXCFile.from_txc_document"
        db = "boilerplate.db.file_processing_result.BodsDB"
        with patch(buf, return_value=mock_txc_file):
            with patch(db, return_value=MockedDB()) as mock_db:
                mock_session = MagicMock()
                mock_db.session.__enter__.return_value = mock_session
                # mock_db.classes.return_value = MagicMock()
                # Call the lambda handler
                lambda_handler(event, None)

        # Assert S3 get_object was called with the correct key
        mock_s3_instance.get_object.assert_called_once_with("4567/test-key")

        # Ensure txc_file_attributes_to_db is called with the correct arguments
        mock_txc_file_attributes_to_db.assert_called_once_with(
            revision_id=123, attributes=[mock_txc_file]
        )

        # Ensure no error was logged
        mock_logger.error.assert_not_called()

    @patch("periodic_tasks.txc_file_data_extractor.logger")
    @patch("periodic_tasks.txc_file_data_extractor.S3")
    @patch("boilerplate.db.file_processing_result.write_error_to_db")
    def test_lambda_handler_no_files(self, mock_err, mock_s3, mock_logger):
        # Event structure with a test bucket and key
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "9876/test-key", "revision_id": 123},
                    }
                }
            ]
        }

        # Mock the S3 handler to return file content
        mock_s3_instance = mock_s3.return_value
        mock_s3_instance.get_object.return_value = BytesIO(b"mock XML content")
        mock_err = mock_err.return_value
        mock_err = MagicMock()

        # Mock TransXChangeDatasetParser to return an empty list, simulating no documents
        doc_ = "periodic_tasks.txc_file_data_extractor.TransXChangeDatasetParser.get_documents"
        db = "boilerplate.db.file_processing_result.BodsDB"
        with patch(doc_, return_value=[]):
            with patch(db, return_value=MockedDB()) as mock_db:
                mock_session = MagicMock()
                mock_db.session.__enter__.return_value = mock_session
                with self.assertRaises(Exception) as context:
                    lambda_handler(event, None)

            # Confirm the exception message contains the expected text
            self.assertIn("No file to process", str(context.exception))
