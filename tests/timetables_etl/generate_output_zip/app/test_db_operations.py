"""
DB Operations Tests
"""

from datetime import UTC, datetime
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from common_layer.aws.step import MapResults
from common_layer.database.client import SqlDB
from common_layer.database.models import (
    DatasetETLTaskResult,
    ETLErrorCode,
    OrganisationDatasetRevision,
    TaskState,
)
from common_layer.enums import FeedStatus
from freezegun import freeze_time

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory
from tests.factories.database.pipelines import DatasetETLTaskResultFactory
from timetables_etl.generate_output_zip.app.db_operations import (
    update_task_and_revision_status,
)
from timetables_etl.generate_output_zip.app.models.model_zip_processing import (
    ProcessingResult,
)


@pytest.fixture(name="m_task_repo")
def m_task_repo_fixture() -> Generator[MagicMock | AsyncMock, Any, None]:
    """
    Mocked Task Repo
    """
    with patch(
        "timetables_etl.generate_output_zip.app.db_operations.ETLTaskResultRepo"
    ) as mocked_repo:
        yield mocked_repo


@pytest.fixture(name="m_revision_repo")
def m_revision_repo_fixture() -> Generator[MagicMock | AsyncMock, Any, None]:
    """
    Mocked Revision Repo
    """
    with patch(
        "timetables_etl.generate_output_zip.app.db_operations.OrganisationDatasetRevisionRepo"
    ) as mocked_repo:

        yield mocked_repo


def assert_expected_repo_calls(
    m_task_repo: MagicMock,
    m_revision_repo: MagicMock,
    task_result: DatasetETLTaskResult,
    revision: OrganisationDatasetRevision,
) -> None:
    """
    Assert task/revision repos are used to fetch and update records
    """
    m_task_repo.return_value.require_by_id.assert_called_once_with(task_result.id)

    # The actual implementation uses mark_success or mark_error, not direct update
    # So we should not assert on update being called

    m_revision_repo.return_value.require_by_id.assert_called_once_with(revision.id)
    m_revision_repo.return_value.update.assert_called_once_with(revision)


def test_update_task_and_revision_status_success(
    m_task_repo: MagicMock, m_revision_repo: MagicMock
) -> None:
    """
    Test that when both map results and processing results are successful
    the task and revision are updated with the expected success states
    """
    task_result = DatasetETLTaskResultFactory.create_with_id(id_number=123)
    m_task_repo.return_value.require_by_id.return_value = task_result

    # Mock the mark_success method to update the task_result directly
    def mock_mark_success(task_id: int) -> None:
        task_result.status = TaskState.SUCCESS.value
        task_result.error_code = ETLErrorCode.EMPTY.value
        task_result.completed = datetime.now(UTC)
        task_result.progress = 100
        task_result.task_name_failed = ""

    m_task_repo.return_value.mark_success.side_effect = mock_mark_success

    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=456)
    m_revision_repo.return_value.require_by_id.return_value = revision

    # Succeeded files in MapResults
    map_results = MapResults(succeeded=[MagicMock()], failed=[])

    # ProcessingResult has successful files
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
            TaskState.FAILURE.value,
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
            TaskState.FAILURE.value,
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
    expected_task_state: str,
    expected_feed_status: str,
    expected_error_code: str,
    expected_additional_info: str,
) -> None:
    """
    Test that when map result contains successful results, but some files failed re-zipping,
    the task and revision are updated with the expected error states
    """
    task_result = DatasetETLTaskResultFactory.create_with_id(id_number=123)
    m_task_repo.return_value.require_by_id.return_value = task_result

    # Mock the mark_error method to update the task_result directly
    def mock_mark_error(
        task_id: int, task_name: str, error_code: ETLErrorCode, additional_info: str
    ) -> None:
        task_result.status = TaskState.FAILURE.value  # Use .value here
        task_result.error_code = error_code.value  # Use .value here
        task_result.additional_info = additional_info
        task_result.completed = datetime.now(UTC)
        task_result.task_name_failed = task_name

    m_task_repo.return_value.mark_error.side_effect = mock_mark_error

    # Mock the mark_success method similarly if needed
    def mock_mark_success(task_id: int) -> None:
        task_result.status = TaskState.SUCCESS.value
        task_result.error_code = ETLErrorCode.EMPTY.value
        task_result.additional_info = ""
        task_result.completed = datetime.now(UTC)
        task_result.progress = 100
        task_result.task_name_failed = ""

    m_task_repo.return_value.mark_success.side_effect = mock_mark_success

    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=456)
    m_revision_repo.return_value.require_by_id.return_value = revision

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
