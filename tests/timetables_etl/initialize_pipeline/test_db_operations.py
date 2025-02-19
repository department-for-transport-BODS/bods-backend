"""
Tests for InitializePipeline db_operations
"""

from datetime import UTC, datetime
from unittest.mock import Mock, create_autospec, patch
from uuid import UUID, uuid4

import pytest
from common_layer.database.client import SqlDB
from common_layer.database.models.model_pipelines import DatasetETLTaskResult, TaskState
from common_layer.database.repos.repo_data_quality import (
    DataQualityPostSchemaViolationRepo,
    DataQualityPTIObservationRepo,
    DataQualitySchemaViolationRepo,
)
from common_layer.database.repos.repo_etl_task import ETLTaskResultRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationTXCFileAttributesRepo,
)
from common_layer.enums import FeedStatus
from common_layer.exceptions.pipeline_exceptions import PipelineException
from initialize_pipeline.app.db_operations import (
    create_task_result,
    delete_existing_txc_file_attributes,
    delete_existing_validation_violations,
    get_and_validate_revision,
    update_revision_status,
)

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


def test_get_and_validate_revision_success(mock_revision_repo):
    """
    Test successful retrieval of revision
    """
    revision_id = 42
    revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=revision_id,
        name="Dev Org_Test Upload_1",
        upload_file="FLIX-FlixBus-UK045-London-Plymouth.xml",
        status="success",
    )
    mock_revision_repo.get_by_id.return_value = revision

    with patch(
        "initialize_pipeline.app.db_operations.OrganisationDatasetRevisionRepo",
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
        "initialize_pipeline.app.db_operations.OrganisationDatasetRevisionRepo",
        return_value=mock_revision_repo,
    ):
        with pytest.raises(PipelineException):
            get_and_validate_revision(Mock(), 99999)

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
        "initialize_pipeline.app.db_operations.OrganisationDatasetRevisionRepo",
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
    task_result = DatasetETLTaskResult(
        revision_id=revision_id, status=TaskState.STARTED, task_id=str(uuid4())
    )
    mock_task_repo.insert.return_value = task_result

    with patch(
        "initialize_pipeline.app.db_operations.ETLTaskResultRepo",
        return_value=mock_task_repo,
    ):
        result = create_task_result(Mock(), revision_id)

        assert result is task_result
        assert result.revision_id == revision_id
        assert result.status == TaskState.STARTED
        assert UUID(result.task_id, version=4)
        mock_task_repo.insert.assert_called_once()


def test_delete_existing_validation_violations():
    """
    Test deleting existing validation violations
    """
    revision_id = 42
    mock_db = create_autospec(SqlDB, instance=True)

    # Mock repositories
    mock_schema_violation_repo = create_autospec(
        DataQualitySchemaViolationRepo, instance=True
    )
    mock_post_schema_violation_repo = create_autospec(
        DataQualityPostSchemaViolationRepo, instance=True
    )
    mock_pti_observation_repo = create_autospec(
        DataQualityPTIObservationRepo, instance=True
    )

    # Mock return values
    mock_schema_violation_repo.delete_by_revision_id.return_value = 3
    mock_post_schema_violation_repo.delete_by_revision_id.return_value = 2
    mock_pti_observation_repo.delete_by_revision_id.return_value = 1

    with patch(
        "initialize_pipeline.app.db_operations.DataQualitySchemaViolationRepo",
        return_value=mock_schema_violation_repo,
    ), patch(
        "initialize_pipeline.app.db_operations.DataQualityPostSchemaViolationRepo",
        return_value=mock_post_schema_violation_repo,
    ), patch(
        "initialize_pipeline.app.db_operations.DataQualityPTIObservationRepo",
        return_value=mock_pti_observation_repo,
    ):
        delete_existing_validation_violations(mock_db, revision_id)

        # Assert delete methods were called with the correct revision ID
        mock_schema_violation_repo.delete_by_revision_id.assert_called_once_with(
            revision_id
        )
        mock_post_schema_violation_repo.delete_by_revision_id.assert_called_once_with(
            revision_id
        )
        mock_pti_observation_repo.delete_by_revision_id.assert_called_once_with(
            revision_id
        )


def test_delete_existing_txc_file_attributes():
    """
    Test deleting existing TXC file attributes
    """
    revision_id = 42
    mock_db = Mock(spec=SqlDB)

    # Create mock repository
    mock_file_attributes_repo = create_autospec(
        OrganisationTXCFileAttributesRepo, instance=True
    )

    # Mock return value for delete operation
    mock_file_attributes_repo.delete_by_revision_id.return_value = 5

    with patch(
        "initialize_pipeline.app.db_operations.OrganisationTXCFileAttributesRepo",
        return_value=mock_file_attributes_repo,
    ):
        delete_existing_txc_file_attributes(mock_db, revision_id)

        # Assert delete method was called with the correct revision ID
        mock_file_attributes_repo.delete_by_revision_id.assert_called_once_with(
            revision_id
        )
