import unittest
from unittest.mock import patch, MagicMock
import os
from lxml import etree

from periodic_tasks.timetable_schema_check import (
    get_transxchange_schema,
    SchemaLoader,
    lambda_handler,
    DatasetTXCValidator,
)


class TestGetTransxchangeSchema(unittest.TestCase):
    @patch("periodic_tasks.timetable_schema_check.get_schema_definition_db_object")
    @patch("periodic_tasks.timetable_schema_check.SchemaLoader")
    def test_get_transxchange_schema_success(
        self, MockSchemaLoader, MockGetSchemaDefinitionDbObject
    ):
        # Arrange
        mock_definition = MagicMock()
        mock_definition.category = "category1"
        mock_definition.schema = "some_schema.zip"
        MockGetSchemaDefinitionDbObject.return_value = mock_definition

        mock_schema_loader = MagicMock()
        MockSchemaLoader.return_value = mock_schema_loader

        mock_schema_loader.schema = "some_schema_object"

        # Act
        result = get_transxchange_schema()

        # Assert
        MockGetSchemaDefinitionDbObject.assert_called_once()
        MockSchemaLoader.assert_called_once_with(
            mock_definition, os.environ["TXC_XSD_PATH"]
        )
        self.assertEqual(result, "some_schema_object")

    @patch("periodic_tasks.timetable_schema_check.get_schema_definition_db_object")
    def test_get_transxchange_schema_missing_definition(
        self, MockGetSchemaDefinitionDbObject
    ):
        # Arrange
        MockGetSchemaDefinitionDbObject.return_value = (
            None  # Simulate missing schema definition
        )

        # Act & Assert
        with self.assertRaises(
            Exception
        ):  # Assuming your code raises an exception on failure
            get_transxchange_schema()


class TestSchemaLoader(unittest.TestCase):

    @patch("periodic_tasks.timetable_schema_check.ZipFile")
    @patch("periodic_tasks.timetable_schema_check.Path.mkdir")
    def test_path_creation_and_extraction(self, MockMkdir, MockZipFile):
        # Arrange
        mock_definition = MagicMock()
        mock_definition.category = "category1"
        mock_definition.schema = "some_schema.zip"

        mock_schema_loader = SchemaLoader(mock_definition, "schema.xsd")

        mock_zip = MagicMock()
        MockZipFile.return_value = mock_zip

        # Mock Path methods
        mock_path = MagicMock()
        mock_path.exists.return_value = False  # Simulate non-existing path
        mock_path.mkdir.return_value = None
        mock_path.open.return_value.__enter__.return_value = MagicMock()

        # Act
        result = (
            mock_schema_loader.path
        )  # Accessing the path property triggers the creation

        # Assert
        MockMkdir.assert_called_once_with(parents=True)
        MockZipFile.assert_called_once_with(mock_definition.schema)
        self.assertTrue(mock_path.mkdir.called)

    @patch("periodic_tasks.timetable_schema_check.ZipFile")
    def test_schema_extraction_error(self, MockZipFile):
        # Arrange
        mock_definition = MagicMock()
        mock_definition.category = "category1"
        mock_definition.schema = "invalid_schema.zip"

        mock_schema_loader = SchemaLoader(mock_definition, "schema.xsd")

        mock_zip = MagicMock()
        MockZipFile.return_value = mock_zip

        mock_zip.extract.side_effect = OSError("Extraction error")

        # Act & Assert
        with self.assertRaises(OSError):
            mock_schema_loader.path  # This triggers extraction


class TestDatasetTXCValidator(unittest.TestCase):

    @patch("periodic_tasks.timetable_schema_check.get_transxchange_schema")
    def test_get_violations_no_violations(self, MockGetTransxchangeSchema):
        # Arrange
        mock_schema = MagicMock()
        MockGetTransxchangeSchema.return_value = mock_schema

        mock_validator = DatasetTXCValidator(revision=MagicMock())

        mock_file = MagicMock()
        mock_doc = etree.Element("root")
        mock_file.seek.return_value = None
        mock_file.read.return_value = "<root></root>"

        mock_schema.validate.return_value = True  # No violations

        # Act
        result = mock_validator.get_violations(mock_file)

        # Assert
        self.assertEqual(result, [])

    @patch("periodic_tasks.timetable_schema_check.get_transxchange_schema")
    def test_get_violations_with_violations(self, MockGetTransxchangeSchema):
        # Arrange
        mock_schema = MagicMock()
        MockGetTransxchangeSchema.return_value = mock_schema

        mock_validator = DatasetTXCValidator(revision=MagicMock())

        mock_file = MagicMock()
        mock_doc = etree.Element("root")
        mock_file.seek.return_value = None
        mock_file.read.return_value = "<root></root>"

        mock_schema.validate.return_value = False  # Simulate violations
        mock_schema.error_log = ["Error 1", "Error 2"]  # Mock violations

        # Act
        result = mock_validator.get_violations(mock_file)

        # Assert
        self.assertEqual(len(result), 2)  # Should contain two violations


class TestLambdaHandler(unittest.TestCase):

    @patch("periodic_tasks.timetable_schema_check.S3")
    @patch("periodic_tasks.timetable_schema_check.get_dataset_revision")
    @patch("periodic_tasks.timetable_schema_check.DatasetTXCValidator")
    @patch("periodic_tasks.timetable_schema_check.SchemaViolation")
    def test_lambda_handler_success(
        self,
        MockSchemaViolation,
        MockDatasetTXCValidator,
        MockGetDatasetRevision,
        MockS3,
    ):
        # Arrange
        mock_s3 = MagicMock()
        MockS3.return_value = mock_s3

        mock_revision = MagicMock()
        MockGetDatasetRevision.return_value = mock_revision

        mock_validator = MagicMock()
        MockDatasetTXCValidator.return_value = mock_validator
        mock_validator.get_violations.return_value = []

        mock_schema_violation = MagicMock()
        MockSchemaViolation.return_value = mock_schema_violation

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "test.xml", "revision_id": 1234},
                    }
                }
            ]
        }

        # Act
        result = lambda_handler(event, None)

        # Assert
        self.assertEqual(result["statusCode"], 200)
        self.assertIn("Successfully ran", result["body"])


if __name__ == "__main__":
    unittest.main()
