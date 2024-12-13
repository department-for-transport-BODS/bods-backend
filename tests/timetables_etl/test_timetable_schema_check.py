import json
import os
import unittest
from io import BytesIO
from unittest.mock import MagicMock, call, patch

from timetables_etl.timetable_schema_check import (
    DatasetTXCValidator,
    SchemaLoader,
    get_transxchange_schema,
    lambda_handler,
)

PREFIX = "timetables_etl.timetable_schema_check"
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
    @patch(f"{PREFIX}.get_schema_definition_db_object")
    @patch(f"{PREFIX}.SchemaLoader")
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

    @patch(f"{PREFIX}.get_schema_definition_db_object")
    @patch.dict("os.environ", TEST_ENV_VAR)
    def test_get_transxchange_schema_missing_definition(
        self, mock_getschemadefinitiondbobject
    ):
        mock_getschemadefinitiondbobject.return_value = None

        with self.assertRaises(Exception):
            get_transxchange_schema()

    @patch(f"{PREFIX}.ZipFile")
    @patch(f"{PREFIX}.Path")
    @patch(f"{PREFIX}.logger")
    def test_path_property(self, mock_logger, mock_path_class, mock_zipfile):
        # Mock definition with category and schema
        mock_definition = MagicMock()
        mock_definition.category = "test_category"
        mock_definition.schema = MagicMock()

        # Mock schema path
        mock_path = MagicMock()
        mock_path.exists.side_effect = [False, False, True]
        mock_path_class.return_value = mock_path

        # Mock directory creation
        mock_directory = MagicMock()
        mock_directory.exists.return_value = False
        mock_directory.mkdir.return_value = None

        # Set up directory and path relationship
        mock_path_class().__truediv__.return_value = mock_directory
        mock_directory.__truediv__.return_value = mock_path

        # Mock ZipFile behavior
        mock_zip_instance = mock_zipfile.return_value.__enter__.return_value
        mock_zip_instance.namelist.return_value = ["file1.xsd", "file2.xsd"]
        mock_zip_instance.extract.side_effect = lambda f, d: None

        # Create SchemaLoader instance
        loader = SchemaLoader(mock_definition, "main.xsd")

        # Invoke the path property
        result = loader.path

        # Assertions for directory creation
        mock_directory.mkdir.assert_called_once_with(parents=True)
        mock_logger.info.assert_called_once_with(f"Directory {mock_directory} created")

        # Assertions for ZipFile usage
        mock_zipfile.assert_called_once_with(mock_definition.schema)
        mock_zip_instance.namelist.assert_called_once()
        mock_zip_instance.extract.assert_has_calls(
            [call("file1.xsd", mock_directory), call("file2.xsd", mock_directory)]
        )

        # Assertions for path
        self.assertEqual(result, mock_path)

        # Test exception during extraction
        mock_zip_instance.extract.side_effect = OSError("Mocked extraction error")
        loader = SchemaLoader(mock_definition, "main.xsd")
        result = loader.path  # Trigger the property again

        # Check logger warning
        mock_logger.warning.assert_any_call(
            "Could not extract file1.xsd - Mocked extraction error"
        )
        mock_logger.warning.assert_any_call(
            "Could not extract file2.xsd - Mocked extraction error"
        )


class TestDatasetTXCValidator(unittest.TestCase):

    @patch(f"{PREFIX}.get_transxchange_schema")
    @patch(f"{PREFIX}.XMLValidator")
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

    @patch(f"{PREFIX}.get_transxchange_schema")
    @patch(f"{PREFIX}.XMLValidator")
    @patch("lxml.etree.parse")
    @patch.dict("os.environ", TEST_ENV_VAR)
    @patch(f"{PREFIX}.BaseSchemaViolation")
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

    @patch(f"{PREFIX}.XMLValidator")
    @patch(f"{PREFIX}.BaseSchemaViolation")
    @patch(f"{PREFIX}.get_transxchange_schema")
    def test_get_violations_with_xml_error(
        self, mock_get_schema, mock_base_violation, mock_xml_validator
    ):
        # Mock revision object
        mock_revision = MagicMock()
        mock_revision.id = 123

        # Mock XMLValidator
        mock_error = MagicMock()
        mock_xml_validator.return_value.dangerous_xml_check.return_value = [mock_error]

        # Mock BaseSchemaViolation
        mock_violation = MagicMock()
        mock_base_violation.from_error.return_value = mock_violation

        # Mock schema
        mock_schema = MagicMock()
        mock_get_schema.return_value = mock_schema

        # Mock file object
        mock_file = BytesIO(b"<invalid>xml</invalid>")

        # Create an instance of DatasetTXCValidator
        validator = DatasetTXCValidator(mock_revision)

        # Call get_violations
        violations = validator.get_violations(mock_file)

        # Assertions
        mock_xml_validator.assert_called_once_with(mock_file)
        mock_base_violation.from_error.assert_called_once_with(
            mock_error, revision_id=123
        )
        self.assertEqual(len(violations), 1)
        self.assertIn(mock_violation, violations)


class TestLambdaHandler(unittest.TestCase):

    @patch(f"{PREFIX}.S3")
    @patch(f"{PREFIX}.get_revision")
    @patch(f"{PREFIX}.DatasetTXCValidator")
    @patch(f"{PREFIX}.SchemaViolation")
    @patch("common_layer.db.file_processing_result.DbManager")
    @patch(f"{PREFIX}.logger")
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
            "Bucket": "test-bucket",
            "ObjectKey": "bodds.zip",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables",
        }

        mock_context = MagicMock()

        # Mock the return values for the various calls
        mock_revision = MagicMock()
        mock_getdatasetrevision.id = 1
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

    @patch(f"{PREFIX}.S3")
    @patch(f"{PREFIX}.get_revision")
    @patch(f"{PREFIX}.DatasetTXCValidator")
    @patch(f"{PREFIX}.SchemaViolation")
    @patch("common_layer.db.file_processing_result.DbManager")
    @patch(f"{PREFIX}.logger")
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
            "Bucket": "test-bucket",
            "ObjectKey": "bodds.zip",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables",
        }
        mock_context = MagicMock()

        # Mock the return values for the various calls
        # Mock get revision
        mock_revision = MagicMock()
        mock_revision.id = 1
        mock_getdatasetrevision.return_value = mock_revision

        # Mock the S3 object and method
        mock_s3_handler = MagicMock()
        mock_s3.return_value = mock_s3_handler
        mock_s3_handler.get_object.side_effect = Exception("S3 Error")

        # Call the lambda_handler function and assert exception handling
        with self.assertRaises(Exception):
            lambda_handler(mock_event, mock_context)
