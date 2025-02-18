"""
Tests for InitialisePipeline Lambda
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from common_layer.database.client import SqlDB
from common_layer.database.models.model_pipelines import DatasetETLTaskResult, TaskState
from common_layer.database.repos.repo_etl_task import ETLTaskResultRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.enums import FeedStatus
from initialize_pipeline.app.initialize_pipeline import (
    InitializePipelineEvent,
    initialize_pipeline,
)

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


@pytest.fixture
def setup_mocks(mocker):
    """
    Sets up mocks for repository classes and dependencies.
    """
    mock_revision_repo = mocker.create_autospec(
        OrganisationDatasetRevisionRepo, instance=True
    )
    mock_task_repo = mocker.create_autospec(ETLTaskResultRepo, instance=True)
    mock_dynamodb = mocker.create_autospec(DynamoDBCache, instance=True)
    mock_data_manager = mocker.create_autospec(FileProcessingDataManager, instance=True)

    # Patch dependencies using mocker.patch.object
    mocker.patch(
        "initialize_pipeline.app.db_operations.OrganisationDatasetRevisionRepo",
        return_value=mock_revision_repo,
    )
    mocker.patch(
        "initialize_pipeline.app.db_operations.ETLTaskResultRepo",
        return_value=mock_task_repo,
    )
    mocker.patch(
        "initialize_pipeline.app.initialize_pipeline.FileProcessingDataManager",
        return_value=mock_data_manager,
    )
    mock_delete_validation_violations = mocker.patch(
        "initialize_pipeline.app.initialize_pipeline.delete_existing_validation_violations",
    )
    mock_delete_txc_attributes = mocker.patch(
        "initialize_pipeline.app.initialize_pipeline.delete_existing_txc_file_attributes",
    )

    return {
        "mock_revision_repo": mock_revision_repo,
        "mock_task_repo": mock_task_repo,
        "mock_dynamodb": mock_dynamodb,
        "mock_data_manager": mock_data_manager,
        "mock_delete_validation_violations": mock_delete_validation_violations,
        "mock_delete_txc_attributes": mock_delete_txc_attributes,
    }


def test_initialize_pipeline(setup_mocks):
    """
    Test initializing the pipeline
    """
    revision_id = 42
    revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=revision_id,
        status="success",
        num_of_bus_stops=7,
        num_of_timing_points=40,
        transxchange_version="2.4",
    )
    setup_mocks["mock_revision_repo"].get_by_id.return_value = revision

    task_result = DatasetETLTaskResult(
        revision_id=revision_id, status=TaskState.STARTED, task_id=str(uuid4())
    )
    setup_mocks["mock_task_repo"].insert.return_value = task_result

    setup_mocks["mock_data_manager"].prefetch_and_cache_data.return_value = None

    event = InitializePipelineEvent(DatasetRevisionId=revision_id)
    mock_db = MagicMock(spec=SqlDB)

    result = initialize_pipeline(mock_db, setup_mocks["mock_dynamodb"], event)

    assert result == task_result
    assert revision.status == FeedStatus.INDEXING.value
    setup_mocks["mock_revision_repo"].update.assert_called_once_with(revision)
    setup_mocks["mock_data_manager"].prefetch_and_cache_data.assert_called_once_with(
        revision
    )
    assert revision.num_of_bus_stops == 7
    assert revision.num_of_timing_points == 40
    assert revision.transxchange_version == "2.4"

    setup_mocks["mock_delete_validation_violations"].assert_called_once_with(
        mock_db, revision_id
    )
    setup_mocks["mock_delete_txc_attributes"].assert_called_once_with(
        mock_db, revision_id
    )
