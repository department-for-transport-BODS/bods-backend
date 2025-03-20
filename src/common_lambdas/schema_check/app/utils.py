"""
Utility functions for Schema Check
"""

from common_layer.exceptions import XMLSyntaxError
from lxml.etree import _Element  # type: ignore
from lxml.etree import QName
from structlog.stdlib import get_logger

from .constants import XMLSchemaType

log = get_logger()

NETEX_NS = "http://www.netex.org.uk/netex"
TRANSXCHANGE_NS = "http://www.transxchange.org.uk/"


def get_tag_string(tag: str | bytes | bytearray | QName) -> str:
    """Convert various tag types to string."""
    if isinstance(tag, QName):
        return str(tag.text)
    if isinstance(tag, (bytes, bytearray)):
        return tag.decode()
    return str(tag)


def get_xml_type(xml_root: _Element) -> tuple[XMLSchemaType, str]:
    """
    Determine if XML is NeTEx or TransXChange and return version.

    Returns: (XMLSchemaType, version)
    """
    tag = get_tag_string(xml_root.tag)

    if f"{{{NETEX_NS}}}PublicationDelivery" == tag:
        version = xml_root.get("version")
        if version is None:
            raise XMLSyntaxError(f"Missing version attribute in {tag}")
        return XMLSchemaType.NETEX, version

    if "TransXChange" in tag:
        version = xml_root.get("SchemaVersion")
        if version is None:
            raise XMLSyntaxError(f"Missing SchemaVersion attribute in {tag}")
        return XMLSchemaType.TRANSXCHANGE, version

    raise XMLSyntaxError(f"Unknown root tag: {tag}")
