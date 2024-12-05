import unittest
from unittest.mock import MagicMock
import pytest
from common_layer.db.repositories.txc_file_attributes import TxcFileAttributesRepository
from common_layer.exceptions.pipeline_exceptions import PipelineException
from tests.mock_db import MockedDB, organisation_txcfileattributes



class TestGet(unittest.TestCase):

    def test_get(self):
        mock_db = MockedDB()

        obj_id = 123
        revision_id = 456
        filename = "filename1.xml"
        txc_file_attributes = organisation_txcfileattributes(
            id=obj_id, revision_id=revision_id, filename=filename
        )
        other_txc_file_attributes = organisation_txcfileattributes(
            id=321, revision_id=678, filename=filename
        )
        with mock_db.session as session:
            session.add(txc_file_attributes)
            session.add(other_txc_file_attributes)
            session.commit()

        repo = TxcFileAttributesRepository(mock_db)
        result = repo.get(revision_id=revision_id, filename=filename)

        assert result is not None
        assert result.id == obj_id
        assert result.revision_id == revision_id
        assert result.filename == filename


    def test_get_not_found(self):
        mock_db = MockedDB()
        repo = TxcFileAttributesRepository(mock_db)
        result = repo.get(revision_id=123)
        assert result is None


    def test_get_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = Exception("DB Exception")
        repo = TxcFileAttributesRepository(mock_db)
        with pytest.raises(PipelineException):
            repo.get(revision_id=123)

class TestGetAll(unittest.TestCase):

    def test_get_all(self):
        mock_db = MockedDB()
        revision_id = 321

        txc_file_attributes = organisation_txcfileattributes(
            id=123, revision_id=revision_id
        )
        txc_file_attributes_2 = organisation_txcfileattributes(
            id=456, revision_id=revision_id
        )
        other_txc_file_attributes = organisation_txcfileattributes(
            id=789, revision_id=678
        )

        with mock_db.session as session:
            session.add(txc_file_attributes)
            session.add(txc_file_attributes_2)
            session.add(other_txc_file_attributes)
            session.commit()

        repo = TxcFileAttributesRepository(mock_db)
        result = repo.get_all(revision_id=revision_id)

        assert len(result) == 2
        assert result[0].id == 123
        assert result[1].id == 456

    def test_get_all_not_found(self):
        mock_db = MockedDB()
        repo = TxcFileAttributesRepository(mock_db)
        result = repo.get_all(revision_id=123)
        assert result == []

    def test_get_all_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = Exception("DB Exception")
        repo = TxcFileAttributesRepository(mock_db)
        with pytest.raises(PipelineException):
            repo.get_all(revision_id=123)


class TestExists(unittest.TestCase):

    def test_exists(self):
        mock_db = MockedDB()
        hash = "dummyhash"
        revision_id = 321

        txc_file_attributes = organisation_txcfileattributes(
            id=123, revision_id=revision_id, hash=hash
        )
        with mock_db.session as session:
            session.add(txc_file_attributes)
            session.commit()

        repo = TxcFileAttributesRepository(mock_db)
        result = repo.exists(revision_id=revision_id, hash=hash)
        assert result is True

    def test_exists_not_found(self):
        mock_db = MockedDB()
        repo = TxcFileAttributesRepository(mock_db)
        result = repo.exists(revision_id=123)
        assert result is False

    def test_get_all_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = Exception("DB Exception")
        repo = TxcFileAttributesRepository(mock_db)
        with pytest.raises(PipelineException):
            repo.exists(revision_id=123)

