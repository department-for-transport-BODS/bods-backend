import json
import unittest
from unittest.mock import patch, MagicMock
import os

from periodic_tasks.timetable_schema_check import (
    get_transxchange_schema,
    lambda_handler,
    DatasetTXCValidator,
)


TEST_ENV_VAR = {
    "PROJECT_ENV": "dev",
    "POSTGRES_HOST": "sample_host",
    "POSTGRES_PORT": "1234",
    "POSTGRES_USER": "sample_user",
    "POSTGRES_PASSWORD": "<PASSWORD>",
    "TXC_XSD_PATH": "TransXChange_general.xsd",
    "POSTGRES_DB": "test_db",
}


class TestGetTransxchangeSchema(unittest.TestCase):
    @patch("periodic_tasks.timetable_schema_check.get_schema_definition_db_object")
    @patch("periodic_tasks.timetable_schema_check.SchemaLoader")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_get_transxchange_schema_success(
        self, mock_schemaloader, mock_getschemadefinitiondbobject
    ):
        mock_definition = MagicMock()
        mock_definition.category = "category1"
        mock_definition.schema = "some_schema.zip"
        mock_getschemadefinitiondbobject.return_value = mock_definition

        mock_schema_loader = MagicMock()
        mock_schemaloader.return_value = mock_schema_loader

        mock_schema_loader.schema = "some_schema_object"

        result = get_transxchange_schema()

        mock_getschemadefinitiondbobject.assert_called_once()
        mock_schemaloader.assert_called_once_with(
            mock_definition, os.environ["TXC_XSD_PATH"]
        )
        self.assertEqual(result, "some_schema_object")

    @patch("periodic_tasks.timetable_schema_check.get_schema_definition_db_object")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_get_transxchange_schema_missing_definition(
        self, mock_getschemadefinitiondbobject
    ):
        mock_getschemadefinitiondbobject.return_value = None

        with self.assertRaises(Exception):
            get_transxchange_schema()


class TestDatasetTXCValidator(unittest.TestCase):

    @patch("periodic_tasks.timetable_schema_check.get_transxchange_schema")
    @patch("periodic_tasks.timetable_schema_check.XMLValidator")
    @patch("lxml.etree.parse")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_get_violations_no_violations(
        self, mock_etree_parse, mock_xmlValidator, mock_gettransxchangeschema
    ):
        # Step 1: Setup mock file object
        mock_file = MagicMock()
        mock_file.read.return_value = b"<root><element>test</element></root>"

        # Step 2: Mock XML parsing behavior
        mock_xml_document = MagicMock()
        mock_etree_parse.return_value = mock_xml_document

        # Step 3: Mock the XMLValidator class and its behavior
        mock_validator = MagicMock()
        mock_xmlValidator.return_value = mock_validator
        mock_validator.dangerous_xml_check.return_value = False

        # Step 4: Mock the schema validation
        mock_schema = MagicMock()
        mock_schema.validate.return_value = True
        mock_schema.error_log = []
        mock_gettransxchangeschema.return_value = mock_schema

        # Step 5: Mock revision
        mock_revision = MagicMock()
        mock_revision.id = 10

        # Step 6: Create the DatasetTXCValidator instance
        validator = DatasetTXCValidator(revision=mock_revision)

        # Step 7: Call the method under test
        result = validator.get_violations(mock_file)

        # Step 8: Assert that no violations were returned
        self.assertEqual(result, [])
        mock_xmlValidator.assert_called_once_with(mock_file)
        mock_validator.dangerous_xml_check.assert_called_once()
        mock_etree_parse.assert_called_once_with(mock_file)
        mock_gettransxchangeschema.assert_called_once()

    @patch("periodic_tasks.timetable_schema_check.get_transxchange_schema")
    @patch("periodic_tasks.timetable_schema_check.XMLValidator")
    @patch("lxml.etree.parse")
    @patch.dict("os.environ", TEST_ENV_VAR)
    @patch("periodic_tasks.timetable_schema_check.BaseSchemaViolation")
    def test_get_violations_with_errors(
        self,
        mock_baseschemaviolation,
        mock_etree_parse,
        mock_xmlvalidator,
        mock_gettransxchangeschema,
    ):
        # Step 1: Setup mock file object
        mock_file = MagicMock()
        mock_file.read.return_value = b"<root><element>test</element></root>"

        # Step 2: Mock XML parsing behavior
        mock_xml_document = MagicMock()
        mock_etree_parse.return_value = mock_xml_document

        # Step 3: Mock the XMLValidator class and its behavior
        mock_validator = MagicMock()
        mock_xmlvalidator.return_value = mock_validator
        mock_validator.dangerous_xml_check.return_value = False

        # Step 4: Mock the schema validation to simulate errors (invalid XML)
        mock_schema = MagicMock()
        mock_schema.validate.return_value = False
        mock_schema.error_log = ["schema_error_1", "schema_error_2"]
        mock_gettransxchangeschema.return_value = mock_schema

        # Step 5: Mock revision
        mock_revision = MagicMock()
        mock_revision.id = 10

        # Step 6: Create the DatasetTXCValidator instance
        validator = DatasetTXCValidator(revision=mock_revision)

        # Mocking BaseSchemaViolation.from_error to return a mocked violation
        mock_violation = MagicMock()
        mock_baseschemaviolation.from_error.return_value = mock_violation

        # Step 7: Call the method under test
        result = validator.get_violations(mock_file)

        # Step 8: Assert that violations were returned
        self.assertEqual(len(result), 2)
        self.assertEqual(mock_baseschemaviolation.from_error.call_count, 2)
        mock_baseschemaviolation.from_error.assert_any_call(
            "schema_error_1", revision_id=10
        )
        mock_baseschemaviolation.from_error.assert_any_call(
            "schema_error_2", revision_id=10
        )

        mock_xmlvalidator.assert_called_once_with(mock_file)
        mock_validator.dangerous_xml_check.assert_called_once()
        mock_etree_parse.assert_called_once_with(mock_file)
        mock_gettransxchangeschema.assert_called_once()


class TestLambdaHandler(unittest.TestCase):

    @patch("periodic_tasks.timetable_schema_check.S3")
    @patch("periodic_tasks.timetable_schema_check.get_dataset_revision")
    @patch("periodic_tasks.timetable_schema_check.DatasetTXCValidator")
    @patch("periodic_tasks.timetable_schema_check.SchemaViolation")
    @patch("db.file_processing_result.BodsDB")
    @patch("periodic_tasks.timetable_schema_check.logger")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_lambda_handler_success(
        self,
        mock_logger,
        mock_db,
        mock_schemaviolation,
        mock_datasettxcvalidator,
        mock_getdatasetrevision,
        mock_s3,
    ):
        # Setup mocks
        mock_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "3456/bodds.zip"},
                    }
                }
            ]
        }
        mock_context = MagicMock()

        # Mock the return values for the various calls
        mock_revision = MagicMock()
        mock_getdatasetrevision.return_value = mock_revision

        # Mock the S3 object and method
        mock_file_object = MagicMock()
        mock_s3_handler = MagicMock()
        mock_s3.return_value = mock_s3_handler
        mock_s3_handler.get_object.return_value = mock_file_object

        # Mock the DatasetTXCValidator and its method
        mock_validator = MagicMock()
        mock_datasettxcvalidator.return_value = mock_validator
        mock_validator.get_violations.return_value = ["violation_1", "violation_2"]

        mock_schema_violation = MagicMock()
        mock_schemaviolation.return_value = mock_schema_violation
        mock_schema_violation.create.return_value = None

        # Call the lambda_handler function
        response = lambda_handler(mock_event, mock_context)

        # Assertions
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Successfully ran the file schema check", response["body"])
        self.assertIn("2 violations", response["body"])

        # Check that the S3 handler was called with the correct bucket and key
        mock_s3.assert_called_once_with(bucket_name="test-bucket")
        mock_s3_handler.get_object.assert_called_once_with(file_path="bodds.zip")

        # Ensure the validator was created and get_violations was called
        mock_datasettxcvalidator.assert_called_once_with(revision=mock_revision)
        mock_validator.get_violations.assert_called_once_with(mock_file_object)

        # Ensure schema violations were created
        mock_schema_violation.create.assert_called_once_with(
            ["violation_1", "violation_2"]
        )

        # Check that logger.info was called
        mock_logger.info.assert_called_with(
            f"Received event:{json.dumps(mock_event, indent=2)}"
        )

    @patch("periodic_tasks.timetable_schema_check.S3")
    @patch("periodic_tasks.timetable_schema_check.get_dataset_revision")
    @patch("periodic_tasks.timetable_schema_check.DatasetTXCValidator")
    @patch("periodic_tasks.timetable_schema_check.SchemaViolation")
    @patch("boilerplate.db.file_processing_result.BodsDB")
    @patch("periodic_tasks.timetable_schema_check.logger")
    @patch.dict("os.environ", {"TEST_ENV_VAR": "value"})
    def test_lambda_handler_exception(
        self,
        mock_logger,
        mock_db,
        mock_schemaviolation,
        mock_datasettxcvalidator,
        mock_getdatasetrevision,
        mock_s3,
    ):
        # Setup mocks
        mock_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "3456/bodds.zip"},
                    }
                }
            ]
        }
        mock_context = MagicMock()

        # Mock the return values for the various calls
        mock_revision = MagicMock()
        mock_getdatasetrevision.return_value = mock_revision

        # Mock the S3 object and method
        mock_s3_handler = MagicMock()
        mock_s3.return_value = mock_s3_handler
        mock_s3_handler.get_object.side_effect = Exception("S3 Error")

        # Call the lambda_handler function and assert exception handling
        with self.assertRaises(Exception):
            lambda_handler(mock_event, mock_context)
