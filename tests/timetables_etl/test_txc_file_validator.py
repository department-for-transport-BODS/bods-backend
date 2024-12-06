from io import BytesIO
import unittest
from unittest.mock import patch, MagicMock
from timetables_etl.txc_file_validator import (
    TimetableFileValidator,
    lambda_handler
)
from exceptions.zip_file_exceptions import *
from exceptions.xml_file_exceptions import *
from tests.mock_db import MockedDB

TEST_MODULE = "timetables_etl.txc_file_validator"
TEST_ENV_VAR = {"PROJECT_ENV": "dev",
                "CLAMAV_HOST": "abc",
                "CLAMAV_PORT": "1234",
                "POSTGRES_HOST": "sample_host",
                "POSTGRES_PORT": "1234",
                "POSTGRES_USER": "sample_user",
                "POSTGRES_PASSWORD": "<PASSWORD>"
                }


class TestTimetableFileValidator(unittest.TestCase):
    @patch(f"{TEST_MODULE}.S3")
    def setUp(self, mock_s3):
        # Mock S3 object and the file it returns
        self.mock_s3 = mock_s3.return_value
        self.mock_s3.get_object.return_value.read.return_value = \
            b"Test content for a file"

        # Create a sample S3 event
        self.event = {
            "Bucket": "bodds-dev",
            "ObjectKey": "22122022105110.zip",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables"
        }

        # Initialize TimetableFileValidator with the mocked S3 object
        self.validator = TimetableFileValidator(self.event)

    def test_is_zip(self):
        """Test if the file is correctly identified as a zip file."""
        # Mock is_zipfile to return True
        with patch(f"{TEST_MODULE}.is_zipfile", return_value=True):
            self.assertTrue(self.validator.is_zip)

    def test_is_not_zip(self):
        """Test if the file is correctly identified as not a zip file."""
        # Mock is_zipfile to return False
        with patch(f"{TEST_MODULE}.is_zipfile", return_value=False):
            self.assertFalse(self.validator.is_zip)

    def test_file_content(self):
        """Test that the file content is retrieved correctly."""
        self.assertEqual(self.validator.file.read(),
                         b"Test content for a file")

    @patch(f"{TEST_MODULE}.ZippedValidator")
    @patch(f"{TEST_MODULE}.XMLValidator")
    def test_validate_zip_with_xml_files(self,
                                         mock_xml_validator,
                                         mock_zipped_validator):
        """Test validation for a zip file containing XML files."""
        # Mock XMLValidator and ZippedValidator behavior
        mock_zipped_validator = mock_zipped_validator.return_value
        mock_zipped_validator.get_files.return_value = ["file1.xml", "file2.xml"]

        # Call validate and ensure no exceptions are raised
        self.validator.validate()
        mock_xml_validator.return_value.dangerous_xml_check.assert_called()

    @patch(f"{TEST_MODULE}.ZippedValidator")
    @patch(f"{TEST_MODULE}.is_zipfile")
    def test_validate_zip(self,
                          mock_is_zipfile,
                          mock_zipped_validator):
        """Test validation for a zip file"""
        mock_is_zipfile.return_value = True

        mock_zipped_instance = mock_zipped_validator.return_value
        mock_zipped_instance.__enter__.return_value = mock_zipped_instance
        mock_zipped_instance.get_files.return_value = ["file1.xml", "file2.xml"]
        mock_zipped_instance.open.side_effect = lambda name: BytesIO(
            b"<xml>mock data</xml>")

        # Call validate and ensure no exceptions are raised
        self.validator.validate()

        self.assertEqual(mock_zipped_instance.validate.call_count, 1)

    @patch(f"{TEST_MODULE}.FileValidator.is_too_large",
           side_effect=ZipValidationException("File too large"))
    def test_file_too_large_exception(self, mock_file_validator_too_large):
        """Test that a ZipValidationException is raised when the file is too large."""
        with self.assertRaises(ZipValidationException):
            self.validator.validate()


class TestLambdaHandler(unittest.TestCase):
    @patch(f"{TEST_MODULE}.TimetableFileValidator")
    @patch("db.file_processing_result.BodsDB")
    @patch("db.file_processing_result.get_revision")
    @patch("db.file_processing_result.get_step")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_lambda_handler_success(self,
                                    mock_get_step,
                                    mock_get_revision,
                                    mock_db,
                                    mock_timetable_file_validator):
        """Test lambda_handler success response when validation passes."""
        # Mock the return values for the various calls
        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        mock_step = MagicMock()
        mock_step.id = 1
        mock_get_step.return_value = mock_step

        mock_db.return_value = MockedDB()


        # Mock TimetableFileValidator to simulate successful validation
        mock_validator = mock_timetable_file_validator.return_value
        mock_validator.validate.return_value = None  # No exception means success

        # Create a sample S3 event
        event = {
            "Bucket": "bodds-dev",
            "ObjectKey": "22122022105110.zip",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables"
        }

        # Call the lambda_handler and verify the response
        response = lambda_handler(event=event, context=None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("File validation completed", response["body"])

    @patch(f"{TEST_MODULE}.TimetableFileValidator")
    @patch("db.file_processing_result.PipelineFileProcessingResult")
    @patch("db.file_processing_result.BodsDB")
    @patch("db.file_processing_result.get_revision")
    @patch("db.file_processing_result.get_step")
    @patch("db.file_processing_result.get_record")
    def test_lambda_handler_zip_validation_exception(self,
                                                     mock_get_record,
                                                     mock_get_step,
                                                     mock_get_revision,
                                                     mock_db,
                                                     mock_pipeline_file_processing,
                                                     mock_timetable_file_validator):
        """Test lambda_handler raises ZipValidationException and logs the error."""
        # Mock TimetableFileValidator to raise ZipValidationException
        mock_validator = mock_timetable_file_validator.return_value

        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        mock_step = MagicMock()
        mock_step.id = 1
        mock_get_step.return_value = mock_step

        for excep in (ZipTooLarge,
                      NestedZipForbidden,
                      NoDataFound):
            mock_validator.validate.side_effect = excep("Zip validation failed")

            event = {
                "Bucket": "bodds-dev",
                "ObjectKey": "22122022105110.zip",
                "DatasetRevisionId": 123,
                "DatasetType": "timetables"
            }
            mock_db.return_value = MockedDB()
            mock_pipeline_file_processing = mock_pipeline_file_processing.return_value
            mock_pipeline_file_processing.return_value.update = None
            # Mock write_processing_step
            write_step = "db.file_processing_result.write_processing_step"
            err_code = "db.file_processing_result.get_file_processing_error_code"

            with (patch(write_step) as mock_step,
                  patch(err_code) as mock_err_code):
                mock_step.return_value = mock_step
                mock_err_code.return_value = MagicMock(id=1)
                # Verify that lambda_handler raises ZipValidationException
                with self.assertRaises(excep):
                    lambda_handler(event=event, context=None)

    @patch(f"{TEST_MODULE}.TimetableFileValidator")
    @patch("db.file_processing_result.PipelineFileProcessingResult")
    @patch("db.file_processing_result.BodsDB")
    @patch("db.file_processing_result.get_revision")
    @patch("db.file_processing_result.get_step")
    @patch("db.file_processing_result.get_record")
    def test_lambda_handler_xml_validation_exception(self,
                                                     mock_get_record,
                                                     mock_get_step,
                                                     mock_get_revision,
                                                     mock_db,
                                                     mock_pipeline_file_processing,
                                                     mock_timetable_file_validator):
        """Test lambda_handler raises XMLValidationException and logs the error."""
        # Mock TimetableFileValidator to raise XMLValidationException
        mock_validator = mock_timetable_file_validator.return_value

        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_get_revision.return_value = mock_revision

        mock_step = MagicMock()
        mock_step.id = 1
        mock_get_step.return_value = mock_step

        for excep in (XMLSyntaxError,
                      DangerousXML,
                      FileTooLarge):
            mock_validator.validate.side_effect = excep("XML validation failed")

            event = {
                "Bucket": "bodds-dev",
                "ObjectKey": "22122022105110.zip",
                "DatasetRevisionId": 123,
                "DatasetType": "timetables"
            }
            mock_db.return_value = MockedDB()
            mock_pipeline_file_processing = mock_pipeline_file_processing.return_value
            mock_pipeline_file_processing.return_value.update = None

            # Mock write_processing_step
            write_step = "db.file_processing_result.write_processing_step"
            err_code = "db.file_processing_result.get_file_processing_error_code"

            with (patch(write_step) as mock_step,
                  patch(err_code) as mock_err_code):
                mock_step.return_value = mock_step
                mock_err_code.return_value = MagicMock(id=1)
                # Verify that lambda_handler raises XMLValidationException
                with self.assertRaises(excep):
                     lambda_handler(event=event, context=None)


if __name__ == "__main__":
    unittest.main()
