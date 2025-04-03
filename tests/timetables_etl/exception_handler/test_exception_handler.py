"""
ExceptionHandler Tests
"""

from typing import Any

import pytest
from common_layer.database.client import SqlDB
from common_layer.database.models import ETLErrorCode
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.enums import FeedStatus
from pytest_mock import MockerFixture

from tests.factories.database import OrganisationDatasetRevisionFactory
from tests.factories.database.pipelines import DatasetETLTaskResultFactory
from timetables_etl.exception_handler.app.exception_handler import lambda_handler


@pytest.fixture()
def setup_mocks(mocker: MockerFixture) -> dict[str, Any]:
    """
    Setup mocks for exception handler lambda
    """

    mock_db = mocker.patch(
        "timetables_etl.exception_handler.app.exception_handler.SqlDB",
        new_callable=lambda: mocker.create_autospec(SqlDB, instance=False),
    )

    mock_task_result_repo = mocker.patch(
        "timetables_etl.exception_handler.app.exception_handler.ETLTaskResultRepo",
        new_callable=lambda: mocker.create_autospec(ETLTaskResultRepo, instance=False),
    )
    task_result = DatasetETLTaskResultFactory.create(revision_id=123)
    mock_task_result_repo.return_value.require_by_id.return_value = task_result

    mock_dataset_revision_repo = mocker.patch(
        "timetables_etl.exception_handler.app.exception_handler.OrganisationDatasetRevisionRepo",
        new_callable=lambda: mocker.create_autospec(
            OrganisationDatasetRevisionRepo, instance=False
        ),
    )
    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=345)
    mock_dataset_revision_repo.require_by_id.return_value = revision

    return {
        "m_db": mock_db.return_value,
        "m_task_result_repo": mock_task_result_repo.return_value,
        "m_dataset_revision_repo": mock_dataset_revision_repo.return_value,
        "task_result": task_result,
    }


ZIP_NOT_FOUND_CAUSE_RAW = (
    '{"errorMessage": "{\\"ErrorCode\\": \\"NO_DATA_FOUND\\", '
    '\\"Cause\\": \\"Zip file contains no XML files.\\", '
    '\\"Context\\": {\\"File\\": \\"/var/task/app/verify_file.py\\", '
    '\\"Line\\": 101, \\"input_file\\": \\"xml_with_syntax_errors.zip\\"}}", '
    '"errorType": "ZipNoDataFound", '
    '"requestId": "831fb4d0-e67b-4089-a675-cab52316ef91", '
    '"stackTrace": ["raise ZipNoDataFound(input_file=filename)\\n"]}'
)


@pytest.mark.parametrize(
    "event,expected_error_code,expected_additional_info",
    [
        pytest.param(
            {
                "Error": "ZipNoDataFound",
                "Cause": ZIP_NOT_FOUND_CAUSE_RAW,
                "DatasetEtlTaskResultId": 4200,
            },
            ETLErrorCode.NO_DATA_FOUND,
            "Zip file contains no XML files.",
            id="Expected error - ZipNoDataFound",
        ),
        pytest.param(
            {
                "Error": "Runtime.ExitError",
                "Cause": '{"errorType":"Runtime.ExitError","errorMessage":"RequestId: d018ab48-c1d6-4075-9721-fe8ee92e458a Error: Runtime exited with error: signal: killed"}',
                "DatasetEtlTaskResultId": 72118,
            },
            ETLErrorCode.SYSTEM_ERROR,
            "RequestId: d018ab48-c1d6-4075-9721-fe8ee92e458a Error: Runtime exited with error: signal: killed",
            id="Unexpected platform error",
        ),
        pytest.param(
            {
                "Error": "Lambda.Unknown",
                "Cause": 'The cause could not be determined because Lambda did not return an error type. Returned payload: {"errorMessage":"2025-03-25T14:59:02.758Z 92f6dcea-87c0-4e89-9a9e-294239bffbb9 Task timed out after 902.11 seconds"}',
                "DatasetEtlTaskResultId": 1234,
            },
            ETLErrorCode.SYSTEM_ERROR,
            'The cause could not be determined because Lambda did not return an error type. Returned payload: {"errorMessage":"2025-03-25T14:59:02.758Z 92f6dcea-87c0-4e89-9a9e-294239bffbb9 Task timed out after 902.11 seconds"}',
            id="Unexpected Lambda Timeout",
        ),
    ],
)
def test_lambda_handler(
    setup_mocks: dict[str, Any],
    event: dict[str, Any],
    expected_error_code: ETLErrorCode,
    expected_additional_info: str,
):
    m_task_result_repo = setup_mocks["m_task_result_repo"]
    m_revision_repo = setup_mocks["m_dataset_revision_repo"]
    task_result = setup_mocks["task_result"]

    result = lambda_handler(event, {})

    assert result == {"statusCode": 200}

    m_task_result_repo.require_by_id.assert_called_once_with(
        event["DatasetEtlTaskResultId"]
    )
    m_revision_repo.require_by_id.assert_called_once_with(task_result.revision_id)

    m_task_result_repo.mark_error.assert_called_once_with(
        task_id=event["DatasetEtlTaskResultId"],
        task_name="Exception Handler Does not Know Failed Task Name",
        error_code=expected_error_code,
        additional_info=expected_additional_info,
    )


@pytest.mark.parametrize(
    "fail_dataset_revision,fail_dataset_etl_task_result",
    [
        pytest.param(True, True, id="Fail both revision and task (default)"),
        pytest.param(False, True, id="Fail task result only"),
        pytest.param(True, False, id="Fail revision only"),
        pytest.param(False, False, id="Fail neither (only log errors)"),
    ],
)
def test_lambda_handler_skip_mark_as_failed(
    setup_mocks: dict[str, Any],
    fail_dataset_revision: bool,
    fail_dataset_etl_task_result: bool,
):
    m_task_result_repo = setup_mocks["m_task_result_repo"]
    m_revision_repo = setup_mocks["m_dataset_revision_repo"]

    event = {
        "Error": "Runtime.ExitError",
        "Cause": "Previous state failed",
        "DatasetEtlTaskResultId": 72118,
        "FailDatasetRevision": fail_dataset_revision,
        "FailDatasetETLTaskResult": fail_dataset_etl_task_result,
    }

    result = lambda_handler(event, {})

    assert result == {"statusCode": 200}

    if fail_dataset_revision:
        m_revision_repo.update.assert_called_once()
        assert m_revision_repo.update.call_args[0][0].status == FeedStatus.ERROR
    else:
        m_revision_repo.update.assert_not_called()

    if fail_dataset_etl_task_result:
        m_task_result_repo.mark_error.assert_called_once()
    else:
        m_task_result_repo.mark_error.assert_not_called()
