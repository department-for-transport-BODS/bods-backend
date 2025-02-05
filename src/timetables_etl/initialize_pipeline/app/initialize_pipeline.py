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
from common_layer.dynamodb.client import DynamoDB
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


def get_and_validate_revision(
    db: SqlDB, revision_id: int
) -> OrganisationDatasetRevision:
    """
    Retrieves and validates the existence of a dataset revision.
    """
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = revision_repo.get_by_id(revision_id)
    if revision is None:
        raise PipelineException(f"DatasetRevision with id {revision_id} not found.")
    return revision


def update_revision_status(db: SqlDB, revision: OrganisationDatasetRevision) -> None:
    """
    Updates the revision status to indexing.
    """
    logger.debug(
        "Setting OrganisationDatasetRevision Status to indexing",
        dataset_revision_id=revision.id,
    )
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision.status = FeedStatus.INDEXING.value
    revision_repo.update(revision)


def create_task_result(db: SqlDB, revision_id: int) -> DatasetETLTaskResult:
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
    return created_task_result


def initialize_pipeline(
    db: SqlDB, dynamodb: DynamoDB, event: InitializePipelineEvent
) -> DatasetETLTaskResult:
    """
    Initializes the pipeline for dataset processing.
    """
    logger.info(
        "Initializing pipeline for DatasetRevision",
        dataset_revision_id=event.DatasetRevisionId,
    )

    revision = get_and_validate_revision(db, event.DatasetRevisionId)

    update_revision_status(db, revision)

    task_result = create_task_result(db, revision.id)

    logger.info(
        "Pre-fetching data for file-level processing", dataset_revision_id=revision.id
    )
    data_manager = FileProcessingDataManager(db, dynamodb)
    data_manager.prefetch_and_cache_data(revision)

    logger.info(
        "Pipeline initialized with DatasetETLTaskResult",
        dataset_etl_task_result_id=task_result.id,
    )
    return task_result


@metrics.log_metrics
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handler for InitializePipeline
    """
    configure_logging(event, context)
    parsed_event = InitializePipelineEvent(**event)

    db = SqlDB()
    dynamodb = DynamoDB()
    created_task_result = initialize_pipeline(db, dynamodb, parsed_event)
    metrics.add_metric(name="PipelineStarts", unit=MetricUnit.Count, value=1)
    ETLTaskResultRepo(db).update_progress(created_task_result.id, 10)
    return {
        "status_code": 200,
        "message": "Pipeline Initialized",
        "DatasetEtlTaskResultId": created_task_result.id,
    }
