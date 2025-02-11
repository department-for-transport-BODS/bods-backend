"""
XML Attribute Parsing Utils
"""

from datetime import datetime
from typing import cast

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..txc.models import ModificationType

log = get_logger()


def parse_xml_attribute(tag: _Element, attribute_name: str) -> str | None:
    """
    Parse an XML attribute from a given tag.
    """
    attribute = tag.get(attribute_name)
    if attribute:
        return attribute
    return None


def parse_xml_datetime(tag: _Element, attribute_name: str) -> datetime | None:
    """
    Parse XML tag into a datetime
    """
    data = parse_xml_attribute(
        tag,
        attribute_name,
    )
    if data:
        try:
            return datetime.fromisoformat(data)
        except ValueError:
            log.warning(
                "Could not parse XML datetime attribute as python datetime",
                attribute_name=attribute_name,
            )
            return None
    return None


def parse_xml_int(tag: _Element, attribute_name: str) -> int | None:
    """
    Parse XML string tag into int
    """
    data = parse_xml_attribute(tag, attribute_name)

    if data:
        try:
            return int(data)
        except ValueError:
            log.warning(
                "Could not parse XML int attribute as int",
                attribute_name=attribute_name,
            )
            return None
    return None


def parse_creation_datetime(tag: _Element) -> datetime | None:
    """
    Get CreationDateTime attribute for a tag
    """

    return parse_xml_datetime(
        tag,
        "CreationDateTime",
    )


def parse_modification_datetime(tag: _Element) -> datetime | None:
    """
    Get ModificationDateTime Attribute for a tag
    """

    return parse_xml_datetime(
        tag,
        "ModificationDateTime",
    )


def parse_modification(tag: _Element) -> ModificationType | None:
    """
    Parse Modification Attr
    """
    modification = parse_xml_attribute(tag, "Modification")
    if modification:
        return cast(ModificationType, modification)
    # log.debug("Unknown Modification Type defaulting to none", modification=modification)
    return None


def parse_revision_number(tag: _Element) -> int | None:
    """
    Parse RevisionNumber Attr
    """
    return parse_xml_int(tag, "RevisionNumber")
