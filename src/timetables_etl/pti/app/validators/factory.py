"""
XMLFilePTIValidator Factory
"""

from common_layer.txc.models.txc_data import TXCData
from pti.app.models import DbClients

from ..constants import PTI_SCHEMA_PATH
from .xml_file import XmlFilePTIValidator


def get_xml_file_pti_validator(
    db_clients: DbClients,
    txc_data: TXCData,
) -> XmlFilePTIValidator:
    """
    Gets a PTI JSON Schema and returns a DatasetPTIValidator.
    """
    with PTI_SCHEMA_PATH.open("r") as f:
        validator = XmlFilePTIValidator(f, db_clients, txc_data)
    return validator
