"""
Lambda function for the Timetable ETL Job
Each invocation handles a single file
"""

from common_layer.database import SqlDB
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from common_layer.txc.models import TXCData
from common_layer.txc.parser.parser_txc import load_xml_data, parse_txc_from_element
from lxml.etree import _Element
from structlog.stdlib import get_logger

from .exception_handler import handle_lambda_errors
from .models import ETLInputData, TaskData
from .pipeline import transform_data

log = get_logger()


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


@handle_lambda_errors
def lambda_handler(event, _):
    """
    Timetable ETL
    """
    configure_logging()
    log.debug("Input Data", data=event)
    input_data = ETLInputData(**event)
    db = SqlDB()
    txc_data = extract_txc_data(input_data.s3_bucket_name, input_data.s3_file_key)

    task_data = get_task_data(input_data, db)
    transform_data(txc_data, task_data, db)
    return {"status_code": 200, "message": "ETL Completed"}
