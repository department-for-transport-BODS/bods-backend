import pytest
from unittest.mock import MagicMock
from src.boilerplate.exception import (
    DatasetETLTaskResult,
    DatasetETLResultCustomeMethods,
    get_etl_task_or_pipeline_exception,
    PipelineException,
    NoResultFound,
    db,
)

# Define a helper function for a mock dataset result
@pytest.fixture
def mock_etl_task():
    task = DatasetETLTaskResult()
    task.status = DatasetETLResultCustomeMethods.PENDING
    task.completed = None
    task.task_name_failed = None
    task.error_code = None
    return task

# Mock the save method
@pytest.fixture
def mock_save_method(mocker):
    return mocker.patch.object(DatasetETLTaskResult, "save", autospec=True)

def test_to_error(mock_etl_task, mock_save_method):
    mock_etl_task.to_error("dataset_validate", "ERROR1")
    assert mock_etl_task.status == DatasetETLResultCustomeMethods.FAILURE
    assert mock_etl_task.task_name_failed == "dataset_validate"
    assert mock_etl_task.error_code == "ERROR1"
    assert mock_save_method.called

def test_handle_general_pipeline_exception(mock_etl_task, mock_save_method, mocker):
    mock_adapter = MagicMock()
    exception = Exception("Test exception")
    with pytest.raises(PipelineException, match="Test exception"):
        mock_etl_task.handle_general_pipeline_exception(
            exception=exception,
            adapter=mock_adapter,
            message="Custom message",
        )
    assert mock_etl_task.status == DatasetETLResultCustomeMethods.FAILURE
    assert mock_etl_task.error_code == DatasetETLTaskResult.SYSTEM_ERROR
    assert mock_etl_task.additional_info == "Custom message"
    mock_adapter.error.assert_called_once_with("Custom message", exc_info=True)
    assert mock_save_method.called

def test_update_progress(mock_etl_task, mock_save_method):
    mock_etl_task.update_progress(50)
    assert mock_etl_task.progress == 50
    assert mock_save_method.called

def test_get_etl_task_or_pipeline_exception_valid(mocker):
    mock_session = mocker.patch.object(db, "session", autospec=True)
    mock_task = MagicMock()
    mock_session.query.return_value.filter_by.return_value.one.return_value = mock_task
    task = get_etl_task_or_pipeline_exception(pk=1)
    assert task == mock_task

def test_get_etl_task_or_pipeline_exception_not_found(mocker):
    mock_session = mocker.patch.object(db, "session", autospec=True)
    mock_session.query.return_value.filter_by.return_value.one.side_effect = NoResultFound
    with pytest.raises(PipelineException, match="DatasetETLTaskResult 999 does not exist."):
        get_etl_task_or_pipeline_exception(pk=999)
