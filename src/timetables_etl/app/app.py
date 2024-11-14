# from logger import logger

from logger import logger
from lxml.etree import _Element
from pydantic import BaseModel
from s3 import S3

from timetables_etl.app.database.repos.exceptions import TaskNotFoundException
from timetables_etl.app.exception_handler import handle_lambda_errors

from .database import BodsDB
from .database.models import DatasetETLTaskResult
from .database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
)
from .txc.parser.parser_txc import load_xml_data, parse_txc_from_element


class ETLInputData(BaseModel):
    """
    Input data for the ETL Function
    """

    revision_id: int
    task_id: int
    s3_bucket_name: str
    s3_file_key: str


def set_logger_context():
    """
    Add the task data to the logger context
    """


def get_txc_xml(s3_bucket_name: str, s3_file_key: str) -> _Element:
    """
    Get the TXC XML Data from S3
    """
    s3_client = S3(s3_bucket_name)
    file_data = s3_client.download_fileobj(s3_file_key)
    logger.info("Downloaded S3 data")
    xml = load_xml_data(file_data)
    logger.info("Parsed XML data")
    return xml


@handle_lambda_errors
def lambda_handler(event, context):
    """
    Timetable ETL
    """
    input_data = ETLInputData(**event)
    logger.info("Template Lambda Function")

    db = BodsDB()
    task_repo = ETLTaskResultRepo(db)
    xml = get_txc_xml(input_data.s3_bucket_name, input_data.s3_file_key)
    parsed_data = parse_txc_from_element(xml)
    logger.info("Parsed Data")
    task = ETLTaskResultRepo(db).get_by_id(input_data.task_id)
    revision = OrganisationDatasetRevisionRepo(db).get_by_id(input_data.revision_id)
    return
