"""
Lambda: InitializePipeline
"""

import os
from uuid import uuid4

from aws_lambda_powertools import Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from common_layer.database.client import SqlDB
from common_layer.database.models.model_pipelines import DatasetETLTaskResult, TaskState
from common_layer.database.repos.repo_etl_task import ETLTaskResultRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.dynamodb.client import DynamoDB
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.enums import FeedStatus
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.json_logging import configure_logging
from pydantic import BaseModel
from structlog.stdlib import get_logger

metrics = Metrics()
tracer = Tracer()
logger = get_logger()


class InitializePipelineEvent(BaseModel):
    """
    Lambda Event Input Data
    """

    DatasetRevisionId: int


def initialize_pipeline(db: SqlDB, dynamodb: DynamoDB, event: InitializePipelineEvent):
    """
    - Set the Revision Status to Indexing
    - Create DatasetETLTaskResult
    - Add Revision to DynamoDB Cache
    """
    logger.info(
        "Initializing pipeline for DatasetRevision",
        dataset_revision_id=event.DatasetRevisionId,
    )
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = revision_repo.get_by_id(event.DatasetRevisionId)
    if revision is None:
        raise PipelineException(
            f"DatasetRevision with id {event.DatasetRevisionId} not found."
        )

    # Set revision status to indexing
    logger.debug("Setting Revision.status to indexing", dataset_revision_id=revision.id)
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
        "Pre-fetching data for file-level processing", dataset_revision_id=revision.id
    )
    data_manager = FileProcessingDataManager(db, dynamodb)
    data_manager.prefetch_and_cache_data(revision)

    logger.info(
        "Pipeline initialized with DatasetETLTaskResult",
        dataset_etl_task_result_id=created_task_result.id,
    )
    return created_task_result.id


@metrics.log_metrics
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """
    Handler for InitializePipeline
    """
    configure_logging(context)
    parsed_event = InitializePipelineEvent(**event)

    db = SqlDB()
    dynamodb = DynamoDB()
    created_task_result_id = initialize_pipeline(db, dynamodb, parsed_event)
    metrics.add_dimension(name="environment", value=os.getenv("PROJECT_ENV", "unknown"))
    metrics.add_metric(name="PipelineStarts", unit=MetricUnit.Count, value=1)
    return {
        "status_code": 200,
        "message": "Pipeline Initialized",
        "DatasetEtlTaskResultId": created_task_result_id,
    }
