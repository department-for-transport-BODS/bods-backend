"""
FileValidation Lambda
"""

from io import BytesIO
from typing import Any

import common_layer.aws.datadog.tracing  # type: ignore # pylint: disable=unused-import
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .models import FileValidationInputData
from .xml_checks import dangerous_xml_check, validate_is_xml_file

log = get_logger()


def get_xml_file_object(s3_bucket: str, s3_key: str) -> BytesIO:
    """
    Download XML from S3
    """
    s3_client = S3(s3_bucket)
    file_obj = s3_client.download_fileobj(s3_key)
    file_size = file_obj.getbuffer().nbytes
    file_obj.seek(0)
    log.info(
        "Downloaded XML file", file_size_bytes=file_size, bucket=s3_bucket, key=s3_key
    )
    return file_obj


def process_file_validation(input_data: FileValidationInputData) -> None:
    """
    Process the file validation
    """
    log.info("Processing file validation", file_name=input_data.s3_file_key)
    validate_is_xml_file(input_data.s3_file_key)
    xml_file_data = get_xml_file_object(
        input_data.s3_bucket_name, input_data.s3_file_key
    )
    dangerous_xml_check(xml_file_data, file_name=input_data.s3_file_key)
    log.info("File validation passed", file_name=input_data.s3_file_key)


@file_processing_result_to_db(step_name=StepName.TXC_FILE_VALIDATOR)
def lambda_handler(
    event: dict[str, Any], _context: LambdaContext
) -> dict[str, str | int]:
    """
    Lambda handler for file validation
    """
    input_data = FileValidationInputData(**event)
    process_file_validation(input_data)
    return {"statusCode": 200, "body": "Completed File Validation"}
