import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from common_layer.db.schema_violation import SchemaViolation, get_schema_violation_obj


class TestSchemaViolation(unittest.TestCase):

    @patch("common_layer.db.schema_violation.get_schema_violation_obj")
    def test_create_success(self, mock_get_schema_violation_obj):
        """
        Test SchemaViolation.create adds records successfully.
        """
        # Mock database and session
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_db.session.__enter__.return_value = mock_session
        mock_violation_obj = MagicMock()

        # Mock the return value of get_schema_violation_obj
        mock_get_schema_violation_obj.return_value = mock_violation_obj

        # Test data
        violations = [
            {
                "revision_id": 1,
                "filename": "file1.xml",
                "line": 10,
                "details": "Error1"
            },
            {
                "revision_id": 1,
                "filename": "file2.xml",
                "line": 20,
                "details": "Error2"
            },
        ]

        # Instantiate and call the method
        schema_violation = SchemaViolation(mock_db)
        result = schema_violation.create(violations)

        # Assertions
        assert result is True
        assert mock_get_schema_violation_obj.call_count == len(violations)
        mock_session.add.assert_called_with(mock_violation_obj)
        mock_session.commit.assert_called()

    @patch("common_layer.db.schema_violation.get_schema_violation_obj")
    @patch("common_layer.db.schema_violation.logger")
    def test_create_failure(self, mock_logger, mock_get_schema_violation_obj):
        """
        Test SchemaViolation.create handles SQLAlchemyError.
        """
        # Mock database and session
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_db.session.__enter__.return_value = mock_session
        mock_violation_obj = MagicMock()

        # Mock the return value of get_schema_violation_obj
        mock_get_schema_violation_obj.return_value = mock_violation_obj

        # Simulate a failure during session.commit
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        # Test data
        violations = [
            {
                "revision_id": 1,
                "filename": "file1.xml",
                "line": 10,
                "details": "Error1"
            },
        ]

        # Instantiate and call the method
        schema_violation = SchemaViolation(mock_db)
        with self.assertRaises(SQLAlchemyError) as context:
            schema_violation.create(violations)

        self.assertEqual(str(context.exception), "Database error")
        # Assertions
        mock_session.add.assert_called_once_with(mock_violation_obj)
        mock_session.rollback.assert_called_once()
        mock_logger.error.assert_called_once_with(
            " Failed to add record Database error", exc_info=True
        )

    def test_get_schema_violation_obj(self):
        """
        Test get_schema_violation_obj returns the expected object.
        """
        # Mock database
        mock_db = MagicMock()
        mock_violation_class = MagicMock()
        mock_db.classes.data_quality_schemaviolation = mock_violation_class

        # Test data
        violation = {
            "revision_id": 1,
            "filename": "file1.xml",
            "line": 10,
            "details": "Error1",
        }

        # Call the function
        result = get_schema_violation_obj(mock_db, **violation)

        # Assertions
        mock_violation_class.assert_called_once_with(
            revision_id=1, filename="file1.xml", line=10, details="Error1"
        )
        assert result == mock_violation_class.return_value


if __name__ == "__main__":
    unittest.main()
