"""
Lambda function for the Timetable ETL Job
Each invocation handles a single file
"""

from typing import Any

from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database import SqlDB
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.download import download_and_parse_txc
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.xml.txc.parser.parser_txc import TXCParserConfig
from structlog.stdlib import get_logger

from .metrics import create_datadog_metrics
from .models import ETLInputData, TaskData
from .pipeline import transform_data

log = get_logger()
metrics = DatadogMetrics(flush_to_log=True)
metrics.set_default_tags(function="ETLProcess")  # type: ignore


PARSER_CONFIG = TXCParserConfig(
    metadata=True,
    services=True,
    operators=True,
    file_hash=True,
    serviced_organisations=True,
    stop_points=True,
    route_sections=True,
    routes=True,
    journey_pattern_sections=True,
    vehicle_journeys=True,
    track_data=True,
)


def get_task_data(input_data: ETLInputData, db: SqlDB) -> TaskData:
    """
    Gather initial information that should be in the database to start the task
    """

    task = ETLTaskResultRepo(db).get_by_id(input_data.task_id)
    if task is None:
        log.critical(
            "Task not found",
            task=task,
        )
        raise ValueError("Missing Task, Revision or File Attributes")
    revision = OrganisationDatasetRevisionRepo(db).get_by_id(task.revision_id)
    file_attributes = OrganisationTXCFileAttributesRepo(db).get_by_id(
        input_data.file_attributes_id
    )

    if revision is None or file_attributes is None:
        log.critical(
            "Required data missing",
            task=task,
            revision=revision,
            file_attributes=file_attributes,
        )
        raise ValueError("Missing Task, Revision or File Attributes")
    return TaskData(
        etl_task=task,
        revision=revision,
        file_attributes=file_attributes,
        input_data=input_data,
    )


@metrics.log_metrics
@file_processing_result_to_db(step_name=StepName.ETL_PROCESS)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Timetable ETL
    """
    log.debug("Input Data", data=event)
    input_data = ETLInputData(**event)
    db = SqlDB()
    stop_point_client = NaptanStopPointDynamoDBClient()
    txc_data = download_and_parse_txc(
        input_data.s3_bucket_name, input_data.s3_file_key, PARSER_CONFIG
    )
    task_data = get_task_data(input_data, db)
    stats = transform_data(txc_data, task_data, db, stop_point_client)
    create_datadog_metrics(metrics, stats)
    return {
        "status_code": 200,
        "message": "ETL Completed",
        "stats": stats.model_dump(),
        "task_data": task_data.model_dump(),
    }
