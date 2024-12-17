import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

from tests.mock_db import MockedDB
from timetables_etl.file_attributes_etl import lambda_handler


class TestLambdaHandler(unittest.TestCase):
    @patch("timetables_etl.file_attributes_etl.logger")
    @patch("timetables_etl.file_attributes_etl.txc_file_attributes_to_db")
    @patch("timetables_etl.file_attributes_etl.TransXChangeDatasetParser")
    @patch("timetables_etl.file_attributes_etl.S3")
    @patch("common_layer.db.file_processing_result.get_revision")
    @patch("common_layer.db.file_processing_result.get_step")
    @patch("timetables_etl.file_attributes_etl.get_revision")
    def test_lambda_handler_success(
        self,
        mock_txc_get_revision,
        mock_get_step,
        mock_get_revision,
        mock_s3,
        mock_parser,
        mock_txc_file_attributes_to_db,
        mock_logger,
    ):
        # Event structure with a test bucket and key
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": "test-key",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables",
        }
        # Mock get revision for TxC attributes
        mock_txc_revision = MagicMock()
        mock_txc_revision.id = 1
        mock_txc_get_revision.return_value = mock_txc_revision

        # Mock get revision
        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        mock_step = MagicMock()
        mock_step.id = 1
        mock_get_step.return_value = mock_step

        # Mock S3 handler's get_object method
        mock_s3_instance = mock_s3.return_value
        mock_s3_instance.get_object.return_value = BytesIO(b"mock XML content")

        # Mock the TransXChangeDatasetParser to return fake documents
        mock_parser_instance = mock_parser.return_value
        mock_doc = MagicMock()
        mock_parser_instance.get_documents.return_value = [mock_doc]

        # Mock TXCFile to simulate parsed data
        mock_txc_file = MagicMock()
        buf = "timetables_etl.file_attributes_etl.TXCFile.from_txc_document"
        db = "common_layer.db.file_processing_result.DbManager"
        with patch(buf, return_value=mock_txc_file):
            with patch(db, return_value=MockedDB()) as mock_db:
                mock_session = MagicMock()
                mock_db.session.__enter__.return_value = mock_session
                # mock_db.classes.return_value = MagicMock()
                # Call the lambda handler
                lambda_handler(event, None)

        # Assert S3 get_object was called with the correct key
        mock_s3_instance.get_object.assert_called_once_with("test-key")

        # Ensure txc_file_attributes_to_db is called with the correct arguments
        mock_txc_file_attributes_to_db.assert_called_once_with(
            revision_id=1, attributes=[mock_txc_file]
        )

        # Ensure no error was logged
        mock_logger.error.assert_not_called()

    @patch("timetables_etl.file_attributes_etl.logger")
    @patch("timetables_etl.file_attributes_etl.S3")
    @patch("common_layer.db.file_processing_result.write_error_to_db")
    @patch("common_layer.db.file_processing_result.get_revision")
    @patch("common_layer.db.file_processing_result.get_step")
    @patch("timetables_etl.file_attributes_etl.get_revision")
    def test_lambda_handler_no_files(
        self,
        mock_txc_get_revision,
        mock_get_step,
        mock_get_revision,
        mock_err,
        mock_s3,
        mock_logger,
    ):
        # Event structure with a test bucket and key
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": "test-key",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables",
        }
        # Mock get revision for TxC attributes
        mock_txc_revision = MagicMock()
        mock_txc_revision.id = 1
        mock_txc_get_revision.return_value = mock_txc_revision

        mock_step = MagicMock()
        mock_step.id = 1
        mock_get_step.return_value = mock_step

        # Mock get revision
        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        # Mock the S3 handler to return file content
        mock_s3_instance = mock_s3.return_value
        mock_s3_instance.get_object.return_value = BytesIO(b"mock XML content")
        mock_err = mock_err.return_value
        mock_err = MagicMock()

        # Mock TransXChangeDatasetParser to return an empty list,
        # simulating no documents
        doc_ = (
            "timetables_etl.file_attributes_etl."
            "TransXChangeDatasetParser.get_documents"
        )
        db = "common_layer.db.file_processing_result.DbManager"
        with patch(doc_, return_value=[]):
            with patch(db, return_value=MockedDB()) as mock_db:
                mock_session = MagicMock()
                mock_db.session.__enter__.return_value = mock_session
                with self.assertRaises(Exception) as context:
                    lambda_handler(event, None)

            # Confirm the exception message contains the expected text
            self.assertIn("No file to process", str(context.exception))
