import pytest
from unittest.mock import MagicMock
from db.repositories.dataset_etl_task_result import DatasetETLTaskResultRepository
from exception import PipelineException
from sqlalchemy.orm.exc import NoResultFound


@pytest.fixture
def mock_db():
    m_db = MagicMock()
    m_session = MagicMock()
    m_db.session.__enter__.return_value = m_session
    return m_db, m_session


def test_get_by_id(mock_db):
    m_db, m_session = mock_db
    etl_task_result_id = 123
    mock_etl_task_result = MagicMock(id=etl_task_result_id)

    m_query = m_session.query
    m_filter_by = m_query.return_value.filter_by
    m_select_one = m_filter_by.return_value.one
    m_select_one.return_value = mock_etl_task_result

    repo = DatasetETLTaskResultRepository(m_db)
    result = repo.get_by_id(etl_task_result_id)

    assert result == mock_etl_task_result
    m_query.assert_called_once_with(m_db.classes.pipelines_datasetetltaskresult)
    m_filter_by.assert_called_once_with(id=etl_task_result_id)
    m_select_one.assert_called_once()


def test_get_by_id_not_found(mock_db):
    m_db, m_session = mock_db
    m_session.query.return_value.filter_by.return_value.one.side_effect = NoResultFound
    repo = DatasetETLTaskResultRepository(m_db)
    with pytest.raises(PipelineException, match="DatasetETLTaskResult 999 does not exist."):
        repo.get_by_id(999)


def test_update(mock_db):
    m_db, m_session = mock_db

    updated_record = MagicMock()

    repo = DatasetETLTaskResultRepository(m_db)
    repo.update(updated_record)

    m_session.add.assert_called_once_with(updated_record)
    m_session.commit.assert_called_once()


def test_update_exception(mock_db):
    m_db, m_session = mock_db

    m_session.commit.side_effect = Exception("Error saving changes")

    updated_record = MagicMock()
    repo = DatasetETLTaskResultRepository(m_db)

    with pytest.raises(PipelineException, match="Failed to update DatasetETLTaskResult: Error saving changes"):
        repo.update(updated_record)

    m_session.rollback.assert_called_once()
