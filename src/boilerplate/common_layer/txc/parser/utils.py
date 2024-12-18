"""
XML Parsing Utils
"""

from lxml.etree import _Element
from structlog.stdlib import get_logger

log = get_logger()


def find_section(xml_data: _Element, section_name: str) -> _Element:
    """
    Get Top Level XML Tag Element
    """
    section = xml_data.find(section_name)
    if section is None:
        error_message = "Top Level tag not found"
        log.warning(error_message, section=section_name)
        raise ValueError(error_message, section_name)
    return section
