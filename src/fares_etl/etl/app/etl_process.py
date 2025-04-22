"""
Lambda function for the Fares ETL Job
Each invocation handles a single file
"""

import os
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from common_layer.xml.netex.models import PublicationDeliveryStructure
from common_layer.xml.netex.parser import parse_netex
from structlog.stdlib import get_logger

from .load.metadata import load_metadata_into_dynamodb
from .models import ETLInputData

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


@file_processing_result_to_db(step_name=StepName.ETL_PROCESS)
def lambda_handler(event: dict[str, Any], _context: LambdaContext):
    """
    Fares ETL
    """
    log.debug("Input Data", data=event)
    input_data = ETLInputData(**event)

    netex_data = get_netex_publication_delivery(
        input_data.s3_bucket_name,
        input_data.s3_file_key,
    )

    load_metadata_into_dynamodb(
        netex_data,
        input_data.task_id,
        os.path.basename(input_data.s3_file_key),
    )

    return {"status_code": 200, "message": "ETL Completed"}
