from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.models.model_pipelines import DatasetETLTaskResult, TaskState
from common_layer.enums import FeedStatus
from common_layer.exceptions.pipeline_exceptions import PipelineException

from timetables_etl.initialize_pipeline import lambda_handler


@patch("timetables_etl.initialize_pipeline.ETLTaskResultRepo")
@patch("timetables_etl.initialize_pipeline.OrganisationDatasetRevisionRepo")
@patch("timetables_etl.initialize_pipeline.SqlDB")
def test_initialize_pipeline_success(m_db, m_revision_repo, m_task_result_repo):
    revision_id = 123
    event = {"DatasetRevisionId": revision_id}

    revision = MagicMock(id=revision_id, status=None)
    m_revision_repo.return_value.get_by_id.return_value = revision

    m_created_etl_task_result = MagicMock(id=321)
    m_task_result_repo.return_value.insert.return_value = m_created_etl_task_result

    result = lambda_handler(event, {})

    assert result == {
        "status_code": 200,
        "message": "Pipeline Initialized",
        "DatasetEtlTaskResultId": 321,
    }

    # DatasetRevision status updated to indexing
    assert m_revision_repo.return_value.update.call_count == 1
    assert m_revision_repo.return_value.update.call_args[0][0] == revision
    assert m_revision_repo.return_value.update.call_args[0][0].id == revision_id
    assert (
        m_revision_repo.return_value.update.call_args[0][0].status
        == FeedStatus.indexing.value
    )

    # DatasetEtlTaskResult created
    assert m_task_result_repo.return_value.insert.call_count == 1
    assert (
        m_task_result_repo.return_value.insert.call_args[0][0].revision_id
        == revision_id
    )
    assert (
        m_task_result_repo.return_value.insert.call_args[0][0].status
        == TaskState.STARTED
    )


@patch("timetables_etl.initialize_pipeline.OrganisationDatasetRevisionRepo")
@patch("timetables_etl.initialize_pipeline.SqlDB")
def test_initialize_pipeline_error(m_db, m_revision_repo):
    event = {"DatasetRevisionId": 123}

    # No revision found
    m_revision_repo.return_value.get_by_id.return_value = None

    with pytest.raises(
        PipelineException, match="DatasetRevision with id 123 not found."
    ):
        lambda_handler(event, {})
