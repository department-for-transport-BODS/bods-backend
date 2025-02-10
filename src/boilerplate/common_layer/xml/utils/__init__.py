"""
Exports
"""

from .xml_utils import find_section
from .xml_utils_attributes import (
    parse_creation_datetime,
    parse_modification,
    parse_modification_datetime,
    parse_revision_number,
    parse_xml_attribute,
    parse_xml_datetime,
    parse_xml_int,
)
from .xml_utils_tags import (
    does_element_exist,
    get_elem_bool_default,
    get_element_bool,
    get_element_date,
    get_element_datetime,
    get_element_int,
    get_element_text,
    get_element_texts,
    get_tag_str,
)

__all__ = [
    # Core XML utilities
    "find_section",
    # Attribute parsing utilities
    "parse_creation_datetime",
    "parse_modification",
    "parse_modification_datetime",
    "parse_revision_number",
    "parse_xml_attribute",
    "parse_xml_datetime",
    "parse_xml_int",
    # Tag/element parsing utilities
    "get_elem_bool_default",
    "get_element_bool",
    "get_element_date",
    "get_element_datetime",
    "get_element_int",
    "get_element_text",
    "get_element_texts",
    "get_tag_str",
    "does_element_exist",
]
