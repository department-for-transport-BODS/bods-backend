"""
Tests for InitialisePipeline Lambda
"""

from datetime import UTC, datetime
from unittest.mock import Mock, create_autospec, patch
from uuid import UUID, uuid4

import pytest
from common_layer.database.models.model_pipelines import DatasetETLTaskResult, TaskState
from common_layer.database.repos.repo_etl_task import ETLTaskResultRepo
from common_layer.enums import FeedStatus
from common_layer.exceptions.pipeline_exceptions import PipelineException
from initialize_pipeline.app.initialize_pipeline import (
    InitializePipelineEvent,
    create_task_result,
    get_and_validate_revision,
    initialize_pipeline,
    update_revision_status,
)

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


def test_get_and_validate_revision_success(mock_revision_repo):
    """
    Test successful retrieval of revision
    """
    revision_id = 42
    revision = OrganisationDatasetRevisionFactory.build(
        id=revision_id,
        name="Dev Org_Test Upload_1",
        upload_file="FLIX-FlixBus-UK045-London-Plymouth.xml",
        status="success",
    )
    mock_revision_repo.get_by_id.return_value = revision

    with patch(
        "initialize_pipeline.app.initialize_pipeline.OrganisationDatasetRevisionRepo",
        return_value=mock_revision_repo,
    ):
        result = get_and_validate_revision(Mock(), revision_id)

        assert result is revision
        assert result.id == revision_id
        assert result.upload_file == "FLIX-FlixBus-UK045-London-Plymouth.xml"
        mock_revision_repo.get_by_id.assert_called_once_with(revision_id)


def test_get_and_validate_revision_not_found(mock_revision_repo):
    """
    Test exception when revision not found
    """
    mock_revision_repo.get_by_id.return_value = None

    with patch(
        "initialize_pipeline.app.initialize_pipeline.OrganisationDatasetRevisionRepo",
        return_value=mock_revision_repo,
    ):
        with pytest.raises(PipelineException) as exc_info:
            get_and_validate_revision(Mock(), 99999)

        assert str(exc_info.value) == "DatasetRevision with id 99999 not found."
        mock_revision_repo.get_by_id.assert_called_once_with(99999)


@pytest.mark.parametrize(
    "initial_status",
    [
        pytest.param("success", id="Updates Status From Success To Indexing"),
        pytest.param("error", id="Updates Status From Error To Indexing"),
    ],
)
def test_update_revision_status(mock_revision_repo, initial_status: str):
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

        assert revision.status == FeedStatus.indexing.value
        mock_revision_repo.update.assert_called_once_with(revision)


def test_create_task_result():
    """
    Test the creation of a task result
    """
    revision_id = 42
    mock_task_repo = create_autospec(ETLTaskResultRepo, instance=True)
    task_result = DatasetETLTaskResult(
        revision_id=revision_id, status=TaskState.STARTED, task_id=str(uuid4())
    )
    mock_task_repo.insert.return_value = task_result

    with patch(
        "initialize_pipeline.app.initialize_pipeline.ETLTaskResultRepo",
        return_value=mock_task_repo,
    ):
        result = create_task_result(Mock(), revision_id)

        assert result is task_result
        assert result.revision_id == revision_id
        assert result.status == TaskState.STARTED
        assert UUID(result.task_id, version=4)
        mock_task_repo.insert.assert_called_once()


def test_initialize_pipeline(mock_revision_repo):
    """
    Test initializing the pipeline
    """
    revision_id = 42
    revision = OrganisationDatasetRevisionFactory.build(
        id=revision_id,
        status="success",
        num_of_bus_stops=7,
        num_of_timing_points=40,
        transxchange_version="2.4",
    )
    mock_revision_repo.get_by_id.return_value = revision

    mock_task_repo = create_autospec(ETLTaskResultRepo, instance=True)
    task_result = DatasetETLTaskResult(
        revision_id=revision_id, status=TaskState.STARTED, task_id=str(uuid4())
    )
    mock_task_repo.insert.return_value = task_result

    mock_dynamodb = create_autospec(
        "common_layer.dynamodb.client.DynamoDB", instance=True
    )
    mock_data_manager = create_autospec(
        "common_layer.dynamodb.data_manager.FileProcessingDataManager", instance=True
    )

    event = InitializePipelineEvent(DatasetRevisionId=revision_id)

    with patch.multiple(
        "initialize_pipeline.app.initialize_pipeline",
        OrganisationDatasetRevisionRepo=lambda db: mock_revision_repo,
        ETLTaskResultRepo=lambda db: mock_task_repo,
        FileProcessingDataManager=lambda db, dynamodb: mock_data_manager,
    ):
        result = initialize_pipeline(Mock(), mock_dynamodb, event)

        assert result == task_result
        assert revision.status == FeedStatus.indexing.value
        mock_revision_repo.update.assert_called_once_with(revision)
        mock_data_manager.prefetch_and_cache_data.assert_called_once_with(revision)
        assert revision.num_of_bus_stops == 7
        assert revision.num_of_timing_points == 40
        assert revision.transxchange_version == "2.4"
