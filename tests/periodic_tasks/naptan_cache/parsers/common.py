"""
Common XML Helpers
"""

from typing import Final

from lxml import etree

NAPTAN_NS: Final[str] = "http://www.naptan.org.uk/"
NAPTAN_PREFIX: Final[str] = "{" + NAPTAN_NS + "}"
NAPTAN_SCHEMA: Final[str] = "http://www.naptan.org.uk/schema/2.1/NaPTAN.xsd"
XSI_NS: Final[str] = "http://www.w3.org/2001/XMLSchema-instance"


def create_stop_point(content: str) -> str:
    """Create a valid NaPTAN StopPoint XML string."""
    return f"""<?xml version="1.0" encoding="windows-1252"?>
        <NaPTAN
            xsi:schemaLocation="{NAPTAN_NS} {NAPTAN_SCHEMA}"
            CreationDateTime="2025-01-08T14:03:49.3633945Z"
            ModificationDateTime="2025-01-08T14:03:49.3713926Z"
            Modification="new"
            FileName="NaPTAN010.xml"
            RevisionNumber="3"
            SchemaVersion="2.1"
            xml:lang="en"
            xmlns:xsi="{XSI_NS}"
            xmlns="{NAPTAN_NS}">
            <StopPoints>
                <StopPoint>
                    {content}
                </StopPoint>
            </StopPoints>
        </NaPTAN>"""


def parse_xml_to_stop_point(xml_str: str) -> etree._Element:
    """Parse XML string to StopPoint element."""
    root = etree.fromstring(xml_str.encode("windows-1252"))
    stop_point = root.find(f".//{NAPTAN_PREFIX}StopPoint")
    if stop_point is None:
        raise ValueError("StopPoint element not found in XML")
    return stop_point
