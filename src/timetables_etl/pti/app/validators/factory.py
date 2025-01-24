"""
XMLFilePTIValidator Factory
"""

from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import NaptanStopPointDynamoDBClient
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.txc.models.txc_data import TXCData

from ..constants import PTI_SCHEMA_PATH
from .xml_file import XmlFilePTIValidator


def get_xml_file_pti_validator(
    dynamodb: DynamoDBCache,
    stop_point_client: NaptanStopPointDynamoDBClient,
    db: SqlDB,
    txc_data: TXCData,
) -> XmlFilePTIValidator:
    """
    Gets a PTI JSON Schema and returns a DatasetPTIValidator.
    """
    with PTI_SCHEMA_PATH.open("r") as f:
        validator = XmlFilePTIValidator(f, dynamodb, stop_point_client, db, txc_data)
    return validator
