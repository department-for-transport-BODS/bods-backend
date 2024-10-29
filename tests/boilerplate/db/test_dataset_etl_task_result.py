import pytest
from unittest.mock import MagicMock, patch
from boilerplate.db.dataset_etl_task_result import DatasetETLTaskResultRepository
from boilerplate.exception import PipelineException
from sqlalchemy.orm.exc import NoResultFound


@pytest.fixture
def mock_db(mocker):
    return mocker.patch("boilerplate.db.dataset_etl_task_result.BodsDB")


@pytest.fixture
def mock_db_session(mock_db):
    m_session = MagicMock()
    mock_db.return_value.session.__enter__.return_value = m_session
    return m_session


def test_get_by_id(mock_db, mock_db_session):
    etl_task_result_id = 123
    mock_etl_task_result = MagicMock(id=etl_task_result_id)

    m_query = mock_db_session.query
    m_filter_by = m_query.return_value.filter_by
    m_select_one = m_filter_by.return_value.one
    m_select_one.return_value = mock_etl_task_result

    result = DatasetETLTaskResultRepository.get_by_id(etl_task_result_id)

    assert result == mock_etl_task_result
    m_query.assert_called_once_with(
        mock_db.return_value.classes.pipelines_datasetetltaskresult
    )
    m_filter_by.assert_called_once_with(id=etl_task_result_id)
    m_select_one.assert_called_once()


def test_get_by_id_not_found(mock_db_session):
    mock_db_session.query.return_value.filter_by.return_value.one.side_effect = (
        NoResultFound
    )
    with pytest.raises(
        PipelineException, match="DatasetETLTaskResult 999 does not exist."
    ):
        DatasetETLTaskResultRepository.get_by_id(999)
