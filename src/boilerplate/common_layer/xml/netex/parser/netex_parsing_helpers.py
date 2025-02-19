"""
Common Helper Functions
"""

from lxml.etree import _Element

from ...utils import parse_xml_attribute


def parse_version_and_id(elem: _Element) -> tuple[str, str]:
    """
    Parse version and id or raise error
    """
    version = parse_xml_attribute(elem, "version")
    if version is None:
        raise ValueError("Missing Version")

    id_code = parse_xml_attribute(elem, "id")
    if id_code is None:
        raise ValueError("Missing Frame ID")
    return version, id_code
