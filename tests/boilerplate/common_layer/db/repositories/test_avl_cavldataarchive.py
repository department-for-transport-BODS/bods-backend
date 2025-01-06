import unittest
from unittest.mock import MagicMock, patch

import pytest
from common_layer.db.repositories.avl_cavldataarchive import (
    get_cavl_db_object,
    update_cavl_db_object,
    update_record_in_db,
)


class TestCavlDbFunctions(unittest.TestCase):

    @patch("common_layer.db.repositories.avl_cavldataarchive.BodsDB")
    def test_get_cavl_db_object_existing_record(self, mock_bodsdb):
        """
        Test get_cavl_db_object retrieves an existing record from the database.
        """
        mock_session = MagicMock()
        mock_cavl_data_archive = MagicMock()

        # Mocking the database session and query
        mock_bodsdb.session.__enter__.return_value = mock_session
        mock_cavl_data_archive.data_format = "JSON"
        mock_session.query.return_value.where.return_value.first.return_value = (
            mock_cavl_data_archive
        )
        mock_bodsdb.classes.avl_cavldataarchive = MagicMock()

        record = get_cavl_db_object(mock_bodsdb, "JSON")

        # Assertions
        mock_session.query.assert_called_once()
        assert record == mock_cavl_data_archive

    @patch("common_layer.db.repositories.avl_cavldataarchive.BodsDB")
    def test_get_cavl_db_object_new_record(self, mock_bodsdb):
        """
        Test get_cavl_db_object creates a new record if none exists in the database.
        """
        mock_session = MagicMock()
        mock_cavl_data_archive_class = MagicMock()

        # Mocking the database session and query
        mock_bodsdb.session.__enter__.return_value = mock_session
        mock_session.query.return_value.where.return_value.first.return_value = None
        mock_bodsdb.classes.avl_cavldataarchive = mock_cavl_data_archive_class

        record = get_cavl_db_object(mock_bodsdb, "CSV")

        # Assertions
        mock_cavl_data_archive_class.assert_called_once()
        assert record is not None

    @patch("common_layer.db.repositories.avl_cavldataarchive.get_cavl_db_object")
    @patch("common_layer.db.repositories.avl_cavldataarchive.update_record_in_db")
    def test_update_cavl_db_object(
        self, mock_update_record_in_db, mock_get_cavl_db_object
    ):
        """
        Test update_cavl_db_object updates the record correctly.
        """
        mock_db = MagicMock()
        mock_archive = MagicMock()

        # Mocking dependent function behavior
        mock_get_cavl_db_object.return_value = mock_archive

        update_cavl_db_object(mock_db, "test_file.json", "JSON")

        # Assertions
        mock_get_cavl_db_object.assert_called_once()
        assert mock_archive.data == "test_file.json"
        mock_update_record_in_db.assert_called_once_with(mock_archive, mock_db)

    def test_update_record_in_db_success(self):
        """
        Test update_record_in_db commits the record successfully.
        """
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_record = MagicMock()

        # Mocking the database session
        mock_db.session.__enter__.return_value = mock_session

        update_record_in_db(mock_record, mock_db)

        # Assertions
        mock_session.add.assert_called_once_with(mock_record)
        mock_session.commit.assert_called_once()

    def test_update_record_in_db_failure(self):
        """
        Test update_record_in_db rolls back on failure.
        """
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_record = MagicMock()

        # Mocking the database session
        mock_db.session.__enter__.return_value = mock_session
        mock_session.commit.side_effect = Exception("Commit failed")

        with pytest.raises(Exception, match="Commit failed"):
            update_record_in_db(mock_record, mock_db)

        # Assertions
        mock_session.add.assert_called_once_with(mock_record)
        mock_session.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
