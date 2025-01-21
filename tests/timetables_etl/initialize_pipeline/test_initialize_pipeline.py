"""
Tests for InitialisePipeline Lambda
"""

from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from common_layer.database.client import SqlDB
from common_layer.database.models.model_pipelines import TaskState
from common_layer.database.repos.repo_etl_task import ETLTaskResultRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.dynamodb.client import DynamoDB
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


@pytest.mark.parametrize(
    "revision_id",
    [
        pytest.param(42, id="Returns When Revision Exists"),
    ],
)
def test_get_and_validate_revision_success(test_db: SqlDB, revision_id: int):
    """
    Test that we are raising an exception when it's not found
    """
    revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=revision_id,
        name="Test Revision",
        status="success",
    )

    with test_db.session_scope() as session:
        session.add(revision)
        session.commit()

    result = get_and_validate_revision(test_db, revision_id)

    assert result is not None
    assert result.id == revision_id


@pytest.mark.parametrize(
    "revision_id",
    [
        pytest.param(99999, id="Raises Exception When Revision Does Not Exist"),
    ],
)
def test_get_and_validate_revision_not_found(test_db: SqlDB, revision_id: int):
    """
    Raising an Exception when it's not found
    """
    with pytest.raises(PipelineException) as exc_info:
        get_and_validate_revision(test_db, revision_id)

    assert str(exc_info.value) == f"DatasetRevision with id {revision_id} not found."


@pytest.mark.parametrize(
    "initial_status",
    [
        pytest.param("success", id="Updates Status From Success To Indexing"),
        pytest.param("error", id="Updates Status From Error To Indexing"),
    ],
)
def test_update_revision_status(test_db: SqlDB, initial_status: str):
    """
    Check that a revision's status can be updated
    """
    # Arrange
    revision = OrganisationDatasetRevisionFactory(status=initial_status)

    with test_db.session_scope() as session:
        session.add(revision)
        session.commit()

    # Act
    update_revision_status(test_db, revision)

    # Assert
    revision_repo = OrganisationDatasetRevisionRepo(test_db)
    updated_revision = revision_repo.get_by_id(revision.id)
    assert updated_revision is not None
    assert updated_revision.status == FeedStatus.indexing.value


@pytest.mark.parametrize(
    "revision_id",
    [
        pytest.param(42, id="Creates Task Result For Existing Revision"),
    ],
)
def test_create_task_result(test_db: SqlDB, revision_id: int):
    """
    Test the creation of a task result
    """
    # Arrange
    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=revision_id)
    with test_db.session_scope() as session:
        session.add(revision)
        session.commit()

    # Act
    task_result = create_task_result(test_db, revision_id)

    # Assert
    assert task_result is not None
    assert task_result.revision_id == revision_id
    assert task_result.status == TaskState.STARTED
    # Verify task_id is a valid UUID
    assert UUID(task_result.task_id, version=4)

    # Verify it's in the database
    task_repo = ETLTaskResultRepo(test_db)
    saved_result = task_repo.get_by_id(task_result.id)
    assert saved_result is not None
    assert saved_result.revision_id == revision_id
    assert saved_result.status == TaskState.STARTED


@pytest.mark.parametrize(
    "revision_id",
    [
        pytest.param(42, id="Initializes Pipeline For Existing Revision"),
    ],
)
def test_initialize_pipeline(test_db: SqlDB, revision_id: int):
    """
    Test Initing the pipeline
    """
    # Arrange
    revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=revision_id,
        status="success",
    )
    with test_db.session_scope() as session:
        session.add(revision)
        session.commit()

    event = InitializePipelineEvent(DatasetRevisionId=revision_id)
    dynamodb = Mock(spec=DynamoDB)

    with patch(
        "timetables_etl.initialize_pipeline.app.initialize_pipeline.FileProcessingDataManager"
    ) as mock_manager:
        # Setup mock for DataManager
        mock_instance = Mock()
        mock_manager.return_value = mock_instance

        # Act
        task_result = initialize_pipeline(test_db, dynamodb, event)

        # Assert
        assert task_result is not None
        assert task_result.revision_id == revision_id

        # Verify data manager was called correctly
        mock_manager.assert_called_once_with(test_db, dynamodb)
        mock_instance.prefetch_and_cache_data.assert_called_once_with(revision)
