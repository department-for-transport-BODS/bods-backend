"""
XMLFilePTIValidator Factory
"""

from common_layer.xml.txc.models import TXCData

from ..constants import PTI_SCHEMA_PATH
from ..models import DbClients
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
