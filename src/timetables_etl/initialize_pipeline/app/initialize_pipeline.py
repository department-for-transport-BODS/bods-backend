"""
Lambda: InitializePipeline
"""

from typing import Any
from uuid import uuid4

from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.aws import configure_metrics
from common_layer.database.client import SqlDB
from common_layer.database.models import (
    DatasetETLTaskResult,
    OrganisationDatasetRevision,
    TaskState,
)
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.enums import FeedStatus
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.json_logging import configure_logging
from pydantic import BaseModel
from structlog.stdlib import get_logger

metrics = configure_metrics()
logger = get_logger()


class InitializePipelineEvent(BaseModel):
    """
    Lambda Event Input Data
    """

    DatasetRevisionId: int
    DatasetETLTaskResultId: int | None = None


def update_revision_status(db: SqlDB, revision: OrganisationDatasetRevision) -> None:
    """
    Updates the revision status to indexing.
    """
    logger.debug(
        "Setting OrganisationDatasetRevision Status to indexing",
        dataset_revision_id=revision.id,
    )
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision.transxchange_version = "2.4"
    revision.status = FeedStatus.INDEXING.value
    revision_repo.update(revision)


def create_task_result(db: SqlDB, revision_id: int) -> int:
    """
    Creates a new ETL task result entry.
    Returns:
        ID of the created task result
    """
    task_result_repo = ETLTaskResultRepo(db)
    task_result = DatasetETLTaskResult(
        revision_id=revision_id,
        status=TaskState.STARTED,
        task_id=str(uuid4()),
    )
    created_task_result = task_result_repo.insert(task_result)
    return created_task_result.id


def initialize_pipeline(
    db: SqlDB, dynamodb: DynamoDBCache, event: InitializePipelineEvent
) -> int:
    """
    Initializes the pipeline for dataset processing.

    Returns: DatasetETLTaskResult ID
    """
    logger.info(
        "Initializing pipeline for DatasetRevision",
        dataset_revision_id=event.DatasetRevisionId,
    )

    revision = OrganisationDatasetRevisionRepo(db).require_by_id(
        event.DatasetRevisionId
    )

    update_revision_status(db, revision)

    # If a DatasetETLTaskResultId is provided, use it, otherwise create one
    # E2E bods will always provide the ID
    # This is to allow us run the statemachine in isolation
    task_result_id = (
        create_task_result(db, revision.id)
        if not event.DatasetETLTaskResultId
        else event.DatasetETLTaskResultId
    )

    logger.info(
        "Pre-fetching data for file-level processing", dataset_revision_id=revision.id
    )
    data_manager = FileProcessingDataManager(db, dynamodb)
    data_manager.prefetch_and_cache_data(revision)

    logger.info(
        "Pipeline initialized with DatasetETLTaskResult",
        dataset_etl_task_result_id=task_result_id,
    )
    return task_result_id


@metrics.log_metrics
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handler for InitializePipeline
    """
    configure_logging(event, context)
    parsed_event = InitializePipelineEvent(**event)

    db = SqlDB()
    dynamodb = DynamoDBCache()
    task_result_id = initialize_pipeline(db, dynamodb, parsed_event)
    metrics.add_metric(name="PipelineStarts", unit=MetricUnit.Count, value=1)
    ETLTaskResultRepo(db).update_progress(task_result_id, 10)
    return {
        "status_code": 200,
        "message": "Pipeline Initialized",
        "DatasetEtlTaskResultId": task_result_id,
    }
