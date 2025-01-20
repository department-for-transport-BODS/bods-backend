"""
FileValidation Lambda
"""

import os
from io import BytesIO
from xml.etree.ElementTree import ElementTree

from aws_lambda_powertools import Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.exceptions.xml_file_exceptions import (
    DangerousXML,
    FileNotXML,
    XMLSyntaxError,
)
from common_layer.s3 import S3
from defusedxml import DefusedXmlException
from defusedxml import ElementTree as detree
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

metrics = Metrics()
tracer = Tracer()
log = get_logger()


class FileValidationInputData(BaseModel):
    """
    Input data for the File Validation
    """

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")


def dangerous_xml_check(file_object: BytesIO, file_name: str) -> ElementTree:
    """
    Parse and check the file object syntax error
    """
    try:
        parsed_xml = detree.parse(
            file_object, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
        log.info(
            "XML successfully validated with no dangerous content",
        )
        return parsed_xml
    except detree.ParseError as err:
        log.error("XML syntax error", exc_info=True)
        raise XMLSyntaxError(file_name, message=err.msg) from err
    except DefusedXmlException as err:
        log.error("Dangerous XML", exc_info=True)
        metrics.add_metric(name="DangerousXMLFound", unit=MetricUnit.Count, value=1)
        raise DangerousXML(file_name, message=err) from err


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


def is_xml_file(file_name: str) -> bool:
    """
    Check file extension ends in .xml
    """
    if not file_name.lower().endswith(".xml"):
        log.error("File is not a xml file", file_name=file_name)
        metrics.add_metric(name="InputFileNotXML", unit=MetricUnit.Count, value=1)
        raise FileNotXML(file_name)
    return True


def process_file_validation(input_data: FileValidationInputData) -> None:
    """
    Process the file validation
    """
    log.info("Processing file validation", file_name=input_data.s3_file_key)
    is_xml_file(input_data.s3_file_key)
    xml_file_data = get_xml_file_object(
        input_data.s3_bucket_name, input_data.s3_file_key
    )
    dangerous_xml_check(xml_file_data, file_name=input_data.s3_file_key)
    log.info("File validation passed", file_name=input_data.s3_file_key)


@metrics.log_metrics
@tracer.capture_lambda_handler
@file_processing_result_to_db(step_name=StepName.TXC_FILE_VALIDATOR)
def lambda_handler(event, _context) -> dict[str, str | int]:
    """
    Lambda handler for file validation
    """
    metrics.add_dimension(name="environment", value=os.getenv("PROJECT_ENV", "unknown"))
    input_data = FileValidationInputData(**event)
    process_file_validation(input_data)
    return {"statusCode": 200, "body": "Completed File Validation"}
