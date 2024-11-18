from unittest.mock import MagicMock, patch
from datetime import datetime

from freezegun import freeze_time
from enums import DatasetETLResultStatus, FeedStatus
from timetables_etl.exception_handler import ErrorInfo, ExceptionEvent, lambda_handler


@patch("timetables_etl.exception_handler.DatasetRevisionRepository")
@patch("timetables_etl.exception_handler.DatasetETLTaskResultRepository")
def test_lambda_handler(m_etl_task_result_repo, m_revision_repo):

    dataset_etl_task_result_id = 123
    dataset_revision_id = 234
    event_payload = ExceptionEvent(
        DatasetEtlTaskResultId=dataset_etl_task_result_id,
        ErrorInfo=ErrorInfo(
            step_name="failed_step_name",
            error_message="Something went wrong"
        )
    )

    dataset_etl_task_result = MagicMock(id=dataset_etl_task_result_id, revision_id=dataset_revision_id)
    m_etl_task_result_repo.return_value.get_by_id.return_value = dataset_etl_task_result

    dataset_revision = MagicMock(id=dataset_revision_id, dataset_id=456)
    m_revision_repo.return_value.get_by_id.return_value = dataset_revision

    with freeze_time("2024-10-12 12:00:00"):
        result = lambda_handler(event_payload.model_dump(), None)

    assert result == {
        'statusCode': 200,
    }

    m_etl_task_result_repo.return_value.get_by_id.assert_called_once_with(dataset_etl_task_result_id)

    assert dataset_etl_task_result.status == DatasetETLResultStatus.FAILURE
    assert dataset_etl_task_result.completed == datetime(2024, 10, 12, 12, 0 ,0)
    assert dataset_etl_task_result.task_name_failed == "failed_step_name"
    assert dataset_etl_task_result.error_code == DatasetETLResultStatus.SYSTEM_ERROR
    assert dataset_etl_task_result.additional_info == "Something went wrong"
    m_etl_task_result_repo.return_value.update.assert_called_once_with(dataset_etl_task_result)

    m_revision_repo.return_value.get_by_id.assert_called_once_with(dataset_revision_id)

    assert dataset_revision.status == FeedStatus.error
    m_revision_repo.return_value.update.assert_called_once_with(dataset_revision)


@patch("timetables_etl.exception_handler.DatasetRevisionRepository")
@patch("timetables_etl.exception_handler.DatasetETLTaskResultRepository")
def test_lambda_handler_already_errored(m_etl_task_result_repo, m_revision_repo):
    """
    If the DatasetETLTaskResult is already in an error state, don't update it
    """
    dataset_etl_task_result_id = 123
    dataset_revision_id = 234
    event_payload = ExceptionEvent(
        DatasetEtlTaskResultId=dataset_etl_task_result_id,
        ErrorInfo=ErrorInfo(
            step_name="failed_step_name",
            error_message="Something went wrong"
        )
    )
    dataset_etl_task_result = MagicMock(id=dataset_etl_task_result_id, revision_id=dataset_revision_id, status=DatasetETLResultStatus.FAILURE.value)
    m_etl_task_result_repo.return_value.get_by_id.return_value = dataset_etl_task_result

    dataset_revision = MagicMock(id=dataset_revision_id, dataset_id=456)
    m_revision_repo.return_value.get_by_id.return_value = dataset_revision

    result = lambda_handler(event_payload.model_dump(), None)

    assert result == {
        'statusCode': 200,
    }
    m_etl_task_result_repo.return_value.update.assert_not_called()
    m_revision_repo.return_value.update.assert_not_called()
