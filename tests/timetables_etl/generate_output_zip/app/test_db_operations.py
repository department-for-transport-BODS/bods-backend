from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.client import SqlDB
from common_layer.database.models import model_transmodel_serviced_organisations
from common_layer.database.models.model_pipelines import ETLErrorCode, TaskState
from common_layer.enums import FeedStatus
from freezegun import freeze_time

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory
from tests.factories.database.pipelines import DatasetETLTaskResultFactory
from timetables_etl.generate_output_zip.app.db_operations import (
    update_task_and_revision_status,
)
from timetables_etl.generate_output_zip.app.models.model_results import MapResults
from timetables_etl.generate_output_zip.app.models.model_zip_processing import (
    ProcessingResult,
)


@pytest.fixture()
def m_task_repo():
    with patch(
        "timetables_etl.generate_output_zip.app.db_operations.ETLTaskResultRepo"
    ) as mocked_repo:
        yield mocked_repo


@pytest.fixture()
def m_revision_repo():
    with patch(
        "timetables_etl.generate_output_zip.app.db_operations.OrganisationDatasetRevisionRepo"
    ) as mocked_repo:
        yield mocked_repo


def assert_expected_repo_calls(m_task_repo, m_revision_repo, task_result, revision):
    """
    Assert task/revision repos are used to fetch and update records
    """
    m_task_repo.return_value.get_by_id.assert_called_once_with(task_result.id)
    m_task_repo.return_value.update.assert_called_once_with(task_result)
    m_revision_repo.return_value.get_by_id.assert_called_once_with(revision.id)
    m_revision_repo.return_value.update.assert_called_once_with(revision)


def test_update_task_and_revision_status_success(m_task_repo, m_revision_repo):
    """
    Test that when both map results and processing results are succuessful
    the task and revision are updated with the expected success states
    """
    task_result = DatasetETLTaskResultFactory.create_with_id(id_number=123)
    m_task_repo.return_value.get_by_id.return_value = task_result

    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=456)
    m_revision_repo.return_value.get_by_id.return_value = revision

    # Suceeded files in MapResults
    map_results = MapResults(succeeded=[MagicMock()], failed=[])

    # ProcessingResult has failed files
    processing_result = ProcessingResult(
        successful_files=1, failed_files=0, output_location="", file_hash=""
    )
    now = datetime.now(UTC)
    with freeze_time(now):
        update_task_and_revision_status(
            db=MagicMock(spec=SqlDB),
            map_results=map_results,
            processing_result=processing_result,
            dataset_etl_task_result_id=task_result.id,
            dataset_revision_id=revision.id,
        )

    # Check updated states
    assert task_result.status == TaskState.SUCCESS.value
    assert task_result.completed == now
    assert task_result.progress == 100
    assert task_result.error_code == ETLErrorCode.EMPTY.value
    assert task_result.task_name_failed == ""

    assert revision.status == FeedStatus.SUCCESS.value

    assert_expected_repo_calls(m_task_repo, m_revision_repo, task_result, revision)


@pytest.mark.parametrize(
    "map_results,processing_result,expected_task_state,expected_feed_status,expected_error_code,expected_additional_info",
    [
        pytest.param(
            MapResults(succeeded=[], failed=[MagicMock()]),
            ProcessingResult(
                successful_files=0, failed_files=0, output_location="", file_hash=""
            ),
            TaskState.FAILURE,
            FeedStatus.ERROR.value,
            ETLErrorCode.NO_VALID_FILE_TO_PROCESS.value,
            "No valid files to process",
            id="No Valid Files",
        ),
        pytest.param(
            MapResults(succeeded=[MagicMock()], failed=[]),
            ProcessingResult(
                successful_files=0, failed_files=1, output_location="", file_hash=""
            ),
            TaskState.FAILURE,
            FeedStatus.ERROR.value,
            ETLErrorCode.SYSTEM_ERROR.value,
            "Files failed during re-zipping process",
            id="Processing Error",
        ),
    ],
)
def test_update_task_and_revision_failures(
    m_task_repo: MagicMock,
    m_revision_repo: MagicMock,
    map_results: MapResults,
    processing_result: ProcessingResult,
    expected_task_state: TaskState,
    expected_feed_status: FeedStatus,
    expected_error_code: ETLErrorCode,
    expected_additional_info: str,
) -> None:
    """
    Test that when map result contains sucessful results, but some files failed re-zipping,
    the task and revision are updated with the expected error states
    """
    task_result = DatasetETLTaskResultFactory.create_with_id(id_number=123)
    m_task_repo.return_value.get_by_id.return_value = task_result

    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=456)
    m_revision_repo.return_value.get_by_id.return_value = revision

    update_task_and_revision_status(
        db=MagicMock(spec=SqlDB),
        map_results=map_results,
        processing_result=processing_result,
        dataset_etl_task_result_id=task_result.id,
        dataset_revision_id=revision.id,
    )

    # Check updated states
    assert task_result.status == expected_task_state
    assert task_result.error_code == expected_error_code
    assert task_result.additional_info == expected_additional_info

    assert revision.status == expected_feed_status

    # Check that repo methods were called as expected
    assert_expected_repo_calls(m_task_repo, m_revision_repo, task_result, revision)
