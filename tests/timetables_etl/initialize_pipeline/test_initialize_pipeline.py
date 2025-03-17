"""
Tests for InitialisePipeline Lambda
"""

from datetime import UTC, datetime
from unittest.mock import Mock, create_autospec, patch
from uuid import uuid4

import pytest
from common_layer.database.models import TaskState
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.enums import FeedStatus
from initialize_pipeline.app.initialize_pipeline import (
    InitializePipelineEvent,
    create_task_result,
    initialize_pipeline,
    update_revision_status,
)

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory
from tests.factories.database.pipelines import DatasetETLTaskResultFactory


@pytest.mark.parametrize(
    "initial_status",
    [
        pytest.param("success", id="Updates Status From Success To Indexing"),
        pytest.param("error", id="Updates Status From Error To Indexing"),
    ],
)
def test_update_revision_status(
    mock_revision_repo: OrganisationDatasetRevisionRepo, initial_status: str
):
    """
    Test revision status update
    """
    current_time = datetime(2024, 1, 1, tzinfo=UTC)
    revision = OrganisationDatasetRevisionFactory.build(
        status=initial_status, modified=current_time, created=current_time
    )

    with patch(
        "initialize_pipeline.app.initialize_pipeline.OrganisationDatasetRevisionRepo",
        return_value=mock_revision_repo,
    ):
        update_revision_status(Mock(), revision)

        assert revision.status == FeedStatus.INDEXING.value
        mock_revision_repo.update.assert_called_once_with(revision)


def test_create_task_result():
    """
    Test the creation of a task result
    """
    revision_id = 42
    mock_task_repo = create_autospec(ETLTaskResultRepo, instance=True)
    task_result_id = 123
    task_result = DatasetETLTaskResultFactory.create_with_id(
        id_number=task_result_id,
        revision_id=revision_id,
        status=TaskState.STARTED,
        task_id=str(uuid4()),
    )
    mock_task_repo.insert.return_value = task_result

    with patch(
        "initialize_pipeline.app.initialize_pipeline.ETLTaskResultRepo",
        return_value=mock_task_repo,
    ):
        result = create_task_result(Mock(), revision_id)

        assert result is task_result_id
        assert mock_task_repo.insert.call_count == 1
        inserted_task = mock_task_repo.insert.call_args[0][0]
        assert inserted_task.revision_id == revision_id
        assert inserted_task.status == TaskState.STARTED


@pytest.mark.parametrize(
    "event_data, should_create_task_result",
    [
        pytest.param(
            {"DatasetRevisionId": 42},
            True,
            id="Only DatasetRevisionId - Create new task",
        ),
        pytest.param(
            {"DatasetRevisionId": 42, "DatasetETLTaskResultId": 321},
            False,
            id="DatasetETLTaskResultId provided - Don't create new task",
        ),
    ],
)
def test_initialize_pipeline(
    mock_revision_repo: OrganisationDatasetRevisionRepo,
    event_data: dict[str, int],
    should_create_task_result: bool,
):
    """
    Test initializing the pipeline
    """
    revision_id = 42
    task_result_id = 321
    revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=revision_id,
        status="success",
        num_of_bus_stops=7,
        num_of_timing_points=40,
        transxchange_version="2.4",
    )
    mock_revision_repo.require_by_id.return_value = revision

    mock_task_repo = create_autospec(ETLTaskResultRepo, instance=True)
    mock_task_repo.insert.return_value = (
        DatasetETLTaskResultFactory.create_with_id(
            id_number=task_result_id,
            revision_id=revision_id,
            status=TaskState.STARTED,
            task_id=str(uuid4()),
        )
        if should_create_task_result
        else None
    )

    mock_dynamodb = create_autospec(
        "common_layer.dynamodb.client.DynamoDBCache", instance=True
    )
    mock_data_manager = create_autospec(FileProcessingDataManager, instance=True)
    mock_data_manager.prefetch_and_cache_data.return_value = None

    event = InitializePipelineEvent(**event_data)

    with patch.multiple(
        "initialize_pipeline.app.initialize_pipeline",
        OrganisationDatasetRevisionRepo=lambda db: mock_revision_repo,
        ETLTaskResultRepo=lambda db: mock_task_repo,
        FileProcessingDataManager=lambda db, dynamodb: mock_data_manager,
    ):
        result = initialize_pipeline(Mock(), mock_dynamodb, event)

        assert result == task_result_id

        if should_create_task_result:
            mock_task_repo.insert.assert_called_once()
        else:
            mock_task_repo.insert.assert_not_called()

        assert revision.status == FeedStatus.INDEXING.value
        mock_revision_repo.update.assert_called_once_with(revision)
        mock_data_manager.prefetch_and_cache_data.assert_called_once_with(revision)
        assert revision.num_of_bus_stops == 7
        assert revision.num_of_timing_points == 40
        assert revision.transxchange_version == "2.4"
