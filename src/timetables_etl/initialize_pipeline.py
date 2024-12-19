from uuid import uuid4

from common_layer.database.client import SqlDB
from common_layer.database.models.model_pipelines import DatasetETLTaskResult, TaskState
from common_layer.database.repos.repo_etl_task import ETLTaskResultRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.enums import FeedStatus
from common_layer.exceptions.pipeline_exceptions import PipelineException
from etl.app.log_setup import configure_logging
from pydantic import BaseModel
from structlog.stdlib import get_logger

logger = get_logger()


class InitializePipelineEvent(BaseModel):
    DatasetRevisionId: int


def initialize_pipeline(db: SqlDB, event: InitializePipelineEvent):
    logger.info(f"Initializing pipeline for DatasetRevision {event.DatasetRevisionId}")
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = revision_repo.get_by_id(event.DatasetRevisionId)
    if revision is None:
        raise PipelineException(
            f"DatasetRevision with id {event.DatasetRevisionId} not found."
        )

    # Set revision status to indexing
    revision.status = FeedStatus.indexing.value
    revision_repo.update(revision)

    # Create DatasetETLTaskResult to track progress
    task_result_repo = ETLTaskResultRepo(db)
    task_result = DatasetETLTaskResult(
        revision_id=revision.id,
        status=TaskState.STARTED,
        task_id=str(uuid4()),
    )
    created_task_result = task_result_repo.insert(task_result)

    logger.info(
        f"Pipeline initialized with DatasetETLTaskResult id {created_task_result.id}"
    )
    return created_task_result.id


def lambda_handler(event, context):
    configure_logging()
    parsed_event = InitializePipelineEvent(**event)

    db = SqlDB()
    created_task_result_id = initialize_pipeline(db, parsed_event)

    return {
        "status_code": 200,
        "message": "Pipeline Initialized",
        "DatasetEtlTaskResultId": created_task_result_id,
    }
