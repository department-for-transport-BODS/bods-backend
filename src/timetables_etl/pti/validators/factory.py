from pathlib import Path

from common_layer.dynamodb.client import DynamoDB

from ..constants import PTI_SCHEMA_PATH
from .xml_file import XmlFilePTIValidator


def get_xml_file_pti_validator(dynamodb: DynamoDB) -> XmlFilePTIValidator:
    """
    Gets a PTI JSON Schema and returns a DatasetPTIValidator.
    """
    with PTI_SCHEMA_PATH.open("r") as f:
        validator = XmlFilePTIValidator(f, dynamodb)
    return validator
