"""
TXC File Metadata
"""

from lxml.etree import _Element

from ..models.txc_metadata import TXCMetadata
from ..models.txc_types import ModificationType


def parse_metadata(xml_data: _Element) -> TXCMetadata:
    """
    Parse Metadata
    """
    modification = xml_data.get("Modification")
    if modification not in ModificationType.__args__:
        modification = None
    return TXCMetadata(
        SchemaVersion=xml_data.get("SchemaVersion"),
        ModificationDateTime=xml_data.get("ModificationDateTime"),
        Modification=modification,
        RevisionNumber=xml_data.get("RevisionNumber"),
        CreationDateTime=xml_data.get("CreationDateTime"),
    )
