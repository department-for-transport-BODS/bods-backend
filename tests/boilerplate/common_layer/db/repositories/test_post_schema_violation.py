import unittest
from unittest.mock import MagicMock, patch

from common_layer.db.repositories.post_schema_violation import PostSchemaViolationRepository, get_post_schema_check_obj
from sqlalchemy.exc import SQLAlchemyError

from tests.mock_db import MockedDB


class TestPostSchemaViolationRepository(unittest.TestCase):
    @patch("common_layer.db.repositories.post_schema_violation.logger")
    def test_create_success(self, mock_logger):
        # Mock the database session and classes
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_db.session.__enter__.return_value = mock_session
        mock_violation_class = MagicMock()
        mock_db.classes.data_quality_postschemaviolation = mock_violation_class

        # Prepare test data
        violations = [
            {"revision_id": 1, "filename": "file1.csv", "details": "Invalid data"},
            {"revision_id": 2, "filename": "file2.csv", "details": "Missing column"},
        ]

        # Instantiate the repository
        repository = PostSchemaViolationRepository(mock_db)

        # Call the create method
        result = repository.create(violations)

        # Assert the method returned True
        self.assertTrue(result)

        # Assert the violations were added and committed
        self.assertEqual(mock_violation_class.call_count, 2)
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

        # Ensure the logger did not log errors
        mock_logger.error.assert_not_called()

    @patch("common_layer.db.repositories.post_schema_violation.logger")
    def test_create_failure(self, mock_logger):
        # Mock the database session and classes
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_db.session.__enter__.return_value = mock_session
        mock_violation_class = MagicMock()
        mock_db.classes.data_quality_postschemaviolation = mock_violation_class

        # Simulate an error during commit
        mock_session.commit.side_effect = SQLAlchemyError("Test SQLAlchemyError")

        # Prepare test data
        violations = [{"revision_id": 1, "filename": "file1.csv", "details": "Invalid data"}]

        # Instantiate the repository
        repository = PostSchemaViolationRepository(mock_db)

        # Assert the create method raises an error
        with self.assertRaises(SQLAlchemyError):
            repository.create(violations)

        # Assert the session rollback was called
        mock_session.rollback.assert_called_once()

        # Ensure the logger logged the error
        mock_logger.error.assert_called_once_with(" Failed to add record Test SQLAlchemyError", exc_info=True)

    def test_get_post_schema_check_obj(self):
        data_ = dict(revision_id=1234, filename="file1.xml", details="Invalid data")
        db = MockedDB()
        ret = get_post_schema_check_obj(db, **data_)
        self.assertTrue(isinstance(ret, db.classes.data_quality_postschemaviolation))


if __name__ == "__main__":
    unittest.main()
