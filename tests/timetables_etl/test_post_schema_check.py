import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

from tests.mock_db import MockedDB
from tests.mock_db import pipeline_processing_step as step_
from timetables_etl.post_schema_check import get_violation, lambda_handler

TEST_ENV_VAR = {
    "PROJECT_ENV": "dev",
    "CLAMAV_HOST": "abc",
    "CLAMAV_PORT": "1234",
    "POSTGRES_HOST": "sample_host",
    "POSTGRES_PORT": "1234",
    "POSTGRES_USER": "sample_user",
    "POSTGRES_PASSWORD": "<PASSWORD>",
}


class TestLambdaHandler(unittest.TestCase):

    @patch("timetables_etl.post_schema_check.DbManager.get_db")
    @patch("timetables_etl.post_schema_check.get_revision")
    @patch("timetables_etl.post_schema_check.get_violation")
    @patch("timetables_etl.post_schema_check.S3")
    @patch(
        "timetables_etl.post_schema_check." "PostSchemaViolationRepository"
    )
    @patch("common_layer.db.file_processing_result.DbManager")
    @patch("common_layer.db.file_processing_result.get_revision")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_lambda_handler_success(
        self,
        mock_get_rev,
        mock_bodds_db,
        mock_post_repo,
        mock_s3,
        mock_get_violation,
        mock_get_revision,
        mock_get_db,
    ):
        """
        Test lambda_handler for a successful run.
        """
        # Mock inputs
        mock_event = {
            "Bucket": "test-bucket",
            "ObjectKey": "test-key",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables",
        }
        mock_context = {}

        # Mock return values
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        xml_content = b'<TransXChange FileName="test.xml">'
        mock_s3_instance = MagicMock()
        mock_s3.return_value = mock_s3_instance
        mock_s3_instance.get_object.return_value = BytesIO(xml_content)

        mock_post_repo_instance = MagicMock()
        mock_post_repo.return_value = mock_post_repo_instance
        mock_get_violation.return_value = "Error"

        mocked_db = MockedDB()
        mock_bodds_db.return_value = mocked_db
        with mocked_db.session as session:
            session.add(
                step_(name="Timetable Post Schema Check", category="TIMETABLES")
            )
            session.commit()
        # m_session = MagicMock()
        mock_bodds_db.session.__enter__.return_value = mocked_db.session

        mock_revision_file_proc = MagicMock()
        mock_revision_file_proc.id = 1
        mock_get_rev.return_value = mock_revision_file_proc

        # Call the lambda handler
        response = lambda_handler(mock_event, mock_context)

        # Assertions
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Successfully ran", response["body"])
        mock_s3_instance.get_object.assert_called_once_with(file_path="test-key")
        mock_post_repo_instance.create.assert_called_once_with(
            filename="test-key", details="Error", revision_id=1
        )

    @patch("timetables_etl.post_schema_check.TransXChangeDocument")
    def test_get_violation_with_pii_error(self, mock_txc_doc):
        """
        Test get_violation detects a PII_ERROR.
        """
        # Mock return value for TransXChangeDocument.get_file_name
        mock_doc_instance = MagicMock()
        mock_doc_instance.get_file_name.return_value = "invalid\\path\\name"
        mock_txc_doc.return_value = mock_doc_instance

        violation = get_violation("mocked-file-content")
        self.assertEqual(violation, "PII_ERROR")

    @patch("timetables_etl.post_schema_check.TransXChangeDocument")
    def test_get_violation_no_error(self, mock_txc_doc):
        """
        Test get_violation returns None when no error is found.
        """
        # Mock return value for TransXChangeDocument.get_file_name
        mock_doc_instance = MagicMock()
        mock_doc_instance.get_file_name.return_value = "valid-path-name"
        mock_txc_doc.return_value = mock_doc_instance

        violation = get_violation("mocked-file-content")
        self.assertIsNone(violation)

    @patch("timetables_etl.post_schema_check.logger.error")
    @patch("timetables_etl.post_schema_check.get_revision")
    @patch("common_layer.db.file_processing_result.DbManager")
    @patch("timetables_etl.post_schema_check.S3")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_lambda_handler_error_handling(
        self, mock_s3, m_db_manager, mock_get_revision, mock_logger
    ):
        """
        Test lambda_handler handles exceptions and logs errors.
        """
        # Mock inputs
        mock_event = {
            "Bucket": "test-bucket",
            "ObjectKey": "test-key",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables",
        }

        mock_context = {}

        # Mock S3 exception
        mock_s3_instance = MagicMock()
        mock_s3.return_value = mock_s3_instance

        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        # Mock return values
        m_db_manager.get_db.return_value = MockedDB()

        # mock_bodds_db.return_value = MockedDB()
        with patch(
            "common_layer.db.file_processing_result.get_revision"
        ) as mock_revision:
            mock_revision.return_value = 123
            with self.assertRaises(Exception) as context:
                lambda_handler(mock_event, mock_context)

                self.assertEqual(
                    "No row was found when one was required", str(context.exception)
                )
