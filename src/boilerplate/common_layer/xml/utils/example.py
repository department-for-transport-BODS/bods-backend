"""
Testing Version getting
"""

from enum import Enum, auto
from pathlib import Path

from lxml import etree
from lxml.etree import QName
from structlog.stdlib import get_logger

log = get_logger()
NETEX_NS = "http://www.netex.org.uk/netex"
TRANSXCHANGE_NS = "http://www.transxchange.org.uk/"


def get_tag_string(tag: str | bytes | bytearray | QName) -> str:
    """Convert various tag types to string"""
    if isinstance(tag, QName):
        return str(tag.text)
    if isinstance(tag, (bytes, bytearray)):
        return tag.decode()
    return str(tag)


class XMLType(Enum):
    """
    Types of Supported XML Document
    """

    NETEX = auto()
    TRANSXCHANGE = auto()


def get_xml_type(filename: Path) -> tuple[XMLType, str]:
    """
    Determine if XML is NeTEx or TransXChange and return version
    Returns XMLType enum
    """
    context = etree.iterparse(
        filename, events=("start",), remove_blank_text=True, remove_comments=True
    )

    # Just get first tag
    _, root = next(context)

    try:
        tag = get_tag_string(root.tag)

        if f"{{{NETEX_NS}}}PublicationDelivery" == tag:
            version = root.get("version")
            if version is None:
                raise ValueError(f"Missing version attribute in {tag}")
            return XMLType.NETEX, version

        if "TransXChange" in tag:
            version = root.get("SchemaVersion")
            if version is None:
                raise ValueError(f"Missing SchemaVersion attribute in {tag}")
            return XMLType.TRANSXCHANGE, version

        raise ValueError(f"Unknown root tag: {tag}")
    finally:
        # Clean up
        root.clear()
        del context


BASE_PATH = Path("/Users/jnakandala/code/demo/bods-backen3/", "data/")

PATH_NETEX = Path(
    BASE_PATH,
    "fares/",
    "BRTB_15_Inbound_AdultSingle_NoTicketValidityPeriod_638743751388925943.xml",
)

PATH_TXC = Path(
    BASE_PATH,
    "txc/"
    "X6-FYSOX06--FSYO-Sheffield-2025-01-19-2025-01-19_SO_FSYO_Locked_f-BODS_V1_1.xml",
)

data = get_xml_type(PATH_NETEX)

log.info("Netex Info", data=data)
data = get_xml_type(PATH_TXC)

log.info("TXC Info", data=data)
