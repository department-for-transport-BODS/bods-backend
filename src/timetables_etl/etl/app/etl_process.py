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
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.s3 import S3
from common_layer.xml.txc.models import TXCData
from common_layer.xml.txc.parser.parser_txc import load_xml_data, parse_txc_from_element
from lxml.etree import _Element
from structlog.stdlib import get_logger

from .models import ETLInputData, ETLProcessStats, TaskData
from .pipeline import transform_data

log = get_logger()
metrics = DatadogMetrics()
metrics.set_default_tags(function="ETLProcess")


def get_txc_xml(s3_bucket_name: str, s3_file_key: str) -> _Element:
    """
    Get the TXC XML Data from S3
    """
    s3_client = S3(s3_bucket_name)
    file_data = s3_client.download_fileobj(s3_file_key)
    log.info("Downloaded S3 data", bucket=s3_bucket_name, key=s3_file_key)
    xml = load_xml_data(file_data)
    log.info("Parsed XML data")
    return xml


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


def extract_txc_data(s3_bucket: str, s3_key: str) -> TXCData:
    """
    Parse and return Pydantic model of TXC Data to process
    """
    xml = get_txc_xml(s3_bucket, s3_key)

    txc_data = parse_txc_from_element(xml)
    log.info("Parsed TXC XML into Pydantic Models")
    return txc_data


def create_datadog_metrics(stats: ETLProcessStats) -> None:
    """
    Send Metrics
    """
    metrics.add_metric(name="ProcessedCountServices", value=stats.services)
    metrics.add_metric(
        name="ProcessedCountBookingArrangements", value=stats.booking_arrangements
    )
    metrics.add_metric(
        name="ProcessedCountServicePatterns", value=stats.booking_arrangements
    )
    metrics.add_metric(
        name="ProcessedCountVehicleJourneys", value=stats.pattern_stats.vehicle_journeys
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
    txc_data = extract_txc_data(input_data.s3_bucket_name, input_data.s3_file_key)

    task_data = get_task_data(input_data, db)
    stats = transform_data(txc_data, task_data, db, stop_point_client)
    create_datadog_metrics(stats)
    return {"status_code": 200, "message": "ETL Completed", "stats": stats.model_dump()}
