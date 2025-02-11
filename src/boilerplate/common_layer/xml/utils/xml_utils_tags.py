"""
Functions to extract info from XML tags
"""

from datetime import date, datetime

from lxml.etree import QName, _Element  # type: ignore
from structlog.stdlib import get_logger

log = get_logger()


def does_element_exist(xml_element: _Element | None, element_name: str) -> bool:
    """
    Check whether element is there
    e.g.
    <StAndrewsDay/>
    """
    if xml_element is None:
        return False
    return xml_element.find(element_name) is not None


def get_element_text(xml_data: _Element, field_name: str) -> str | None:
    """
    Get XML Tag Text Value as string
    """
    element = xml_data.find(field_name)
    if element is not None:
        return element.text
    return None


def get_element_texts(xml_data: _Element, field_name: str) -> list[str]:
    """
    Get a list of text values from multiple XML tags with the same name.
    """
    elements = xml_data.findall(field_name)
    if elements:
        return [element.text for element in elements if element.text]
    return []


def get_element_int(xml_data: _Element, field_name: str) -> int | None:
    """
    Get Element Value as an int
    """
    text = get_element_text(xml_data, field_name)
    if text is not None:
        try:
            return int(text)
        except ValueError:
            log.info(
                "Failed to Parse integer XML as int", field_name=field_name, value=text
            )
    return None


def get_element_datetime(xml_data: _Element, field_name: str) -> datetime | None:
    """
    Get element value as datetime
    """
    text = get_element_text(xml_data, field_name)
    if text is not None:
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            log.warning("Failed to parse datetime", date_str=text)
    return None


def get_element_date(xml_data: _Element, field_name: str) -> date | None:
    """
    Get a date type from a xml element
    """
    text = get_element_text(xml_data, field_name)

    if text is not None:
        try:
            return date.fromisoformat(text)
        except ValueError:
            log.warning("Failed to parse date", date_str=text)
    return None


def get_element_bool(
    xml_data: _Element,
    field_name: str,
) -> bool | None:
    """
    Try getting Element Value as bool
    """
    text = get_element_text(xml_data, field_name)
    if text is not None:
        if text == "true":
            return True
        if text == "false":
            return False
    return None


def get_elem_bool_default(xml_data: _Element, field_name: str, default: bool = False):
    """
    Get element bool but return a default bool value instead of None
    """
    value = get_element_bool(xml_data, field_name)

    if value is None:
        return default

    return value


def get_tag_str(xml_data: _Element) -> str | None:
    """Get the String of a tag"""
    tag = xml_data.tag
    if isinstance(tag, QName):
        return tag.text
    return str(tag)
