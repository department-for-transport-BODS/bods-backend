"""
Lambda function for the Fares ETL Job
Each invocation handles a single file
"""

import os
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database import SqlDB
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from common_layer.xml.netex.models.netex_publication_delivery import (
    PublicationDeliveryStructure,
)
from common_layer.xml.netex.parser.netex_publication_delivery import parse_netex
from structlog.stdlib import get_logger

from .load.data_catalogue import load_data_catalogue
from .load.dataset import load_dataset
from .load.metadata import load_metadata
from .models import ETLInputData, TaskData

log = get_logger()


def get_netex_publication_delivery(
    s3_bucket_name: str, s3_file_key: str
) -> PublicationDeliveryStructure:
    """
    Get the NeTEx XML Data from S3 and parse it
    """
    s3_client = S3(s3_bucket_name)
    file_data = s3_client.download_fileobj(s3_file_key)
    log.info("Downloaded S3 data", bucket=s3_bucket_name, key=s3_file_key)
    xml = parse_netex(file_data)
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

    if revision is None:
        log.critical(
            "Required data missing",
            task=task,
            revision=revision,
        )
        raise ValueError("Missing Task or Revision")
    return TaskData(
        etl_task=task,
        revision=revision,
        input_data=input_data,
    )


@file_processing_result_to_db(step_name=StepName.ETL_PROCESS)
def lambda_handler(event: dict[str, Any], _context: LambdaContext):
    """
    Fares ETL
    """
    log.debug("Input Data", data=event)
    input_data = ETLInputData(**event)
    db = SqlDB()

    netex_data = get_netex_publication_delivery(
        input_data.s3_bucket_name,
        input_data.s3_file_key,
    )

    task_data = get_task_data(input_data, db)

    metadata_dataset_id = load_dataset(
        task_data,
        netex_data.version,
        db,
    )
    metadata_id = load_metadata(
        netex_data,
        metadata_dataset_id,
        db,
    )
    load_data_catalogue(
        netex_data,
        metadata_id,
        os.path.basename(input_data.s3_file_key),
        db,
    )

    return {"status_code": 200, "message": "ETL Completed"}
