"""
Lambda: InitializePipeline
"""

from typing import Any

from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.aws import configure_metrics
from common_layer.database.client import SqlDB
from common_layer.database.models import DatasetETLTaskResult
from common_layer.database.repos import ETLTaskResultRepo
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.json_logging import configure_logging
from pydantic import BaseModel
from structlog.stdlib import get_logger

from .db_operations import (
    create_task_result,
    delete_existing_txc_file_attributes,
    delete_existing_validation_violations,
    get_and_validate_revision,
    update_revision_status,
)

metrics = configure_metrics()
logger = get_logger()


class InitializePipelineEvent(BaseModel):
    """
    Lambda Event Input Data
    """

    DatasetRevisionId: int


def initialize_pipeline(
    db: SqlDB, dynamodb: DynamoDBCache, event: InitializePipelineEvent
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
    delete_existing_validation_violations(db, revision.id)
    delete_existing_txc_file_attributes(db, revision.id)

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
    dynamodb = DynamoDBCache()
    created_task_result = initialize_pipeline(db, dynamodb, parsed_event)
    metrics.add_metric(name="PipelineStarts", unit=MetricUnit.Count, value=1)
    ETLTaskResultRepo(db).update_progress(created_task_result.id, 10)
    return {
        "status_code": 200,
        "message": "Pipeline Initialized",
        "DatasetEtlTaskResultId": created_task_result.id,
    }
