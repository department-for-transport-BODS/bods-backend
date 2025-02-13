"""
Parsing Utilities
"""

from datetime import datetime, timedelta

from lxml.etree import _Element  # type: ignore

from ..models import MultilingualString
from ..models.netex_utility import VersionedRef


def remove_element_from_memory(elem: _Element) -> None:
    """Clean up processed element and its ancestors to free memory."""
    elem.clear()
    parent = elem.getparent()
    if parent is not None:
        previous = elem.getprevious()
        while previous is not None:
            parent.remove(previous)
            previous = elem.getprevious()


def parse_timestamp(elem: _Element) -> datetime | None:
    """
    Parse Timestamp element
    """

    if elem.text:
        return datetime.fromisoformat(elem.text.replace("Z", "+00:00"))
    return None


def parse_timedelta(elem: _Element) -> timedelta | None:
    """
    Parse Timedeltas
    """
    if elem.text:
        return timedelta(seconds=float(elem.text))
    return None


def parse_multilingual_string(elem: _Element) -> MultilingualString | None:
    """Parse Description element."""
    if elem.text:

        return MultilingualString(
            value=elem.text, lang=elem.get("lang"), textIdType=elem.get("textIdType")
        )
    return None


def parse_versioned_ref(elem: _Element) -> VersionedRef:
    """Parse element as VersionedRef."""
    return VersionedRef(
        version=elem.get("version", "1.0"),
        ref=elem.get("ref", ""),
    )
