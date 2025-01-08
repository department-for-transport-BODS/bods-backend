from io import BytesIO

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

log = get_logger()


class FileValidationInputData(BaseModel):
    """
    Input data for the File Validation
    """

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")


def dangerous_xml_check(file_object: BytesIO):
    """
    Parse and check the file object syntax error
    """
    try:
        detree.parse(
            file_object, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
    except detree.ParseError as err:
        log.error("XML syntax error", exc_info=True)
        raise XMLSyntaxError(file_object.name, message=err.msg) from err
    except DefusedXmlException as err:
        log.error("Dangerous XML", exc_info=True)
        raise DangerousXML(file_object.name, message=err) from err


def get_xml_file_object(s3_bucket: str, s3_key: str) -> BytesIO:
    """
    Download XML from S3
    """
    s3_client = S3(s3_bucket)
    return s3_client.download_fileobj(s3_key)


def is_xml_file(file_name: str) -> bool:
    """
    Check file name whether its a xml file
    """
    if not file_name.lower().endswith(".xml"):
        log.error("File is not a xml file", file_name=file_name)
        raise FileNotXML(file_name)
    return True


def process_file_validation(input_data: FileValidationInputData):
    """
    Process the file validation
    """
    log.info("Processing file validation", file_name=input_data.s3_file_key)
    try:
        is_xml_file(input_data.s3_file_key)
        dangerous_xml_check(
            get_xml_file_object(input_data.s3_bucket_name, input_data.s3_file_key)
        )
    except Exception as excep:
        raise excep
    log.info("File validation passed")


@file_processing_result_to_db(step_name=StepName.TXC_FILE_VALIDATOR)
def lambda_handler(event, _):
    """
    Lambda handler for file validation
    """
    process_file_validation(FileValidationInputData(**event))
    return {"statusCode": 200, "body": "Completed File Validation"}
