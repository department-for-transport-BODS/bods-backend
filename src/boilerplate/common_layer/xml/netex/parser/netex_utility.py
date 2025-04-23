"""
Parsing Utilities
"""

from datetime import UTC, datetime, timedelta

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..models import FromToDate, MultilingualString
from ..models.netex_utility import VersionedRef
from .netex_constants import NETEX_NS

log = get_logger()


def get_netex_element(xml_data: _Element, element_name: str) -> _Element | None:
    """Find element in NeTEx namespace"""
    try:
        return xml_data.find(f"{{{NETEX_NS}}}{element_name}")
    except Exception:
        print(f"Could not find element: {element_name}")
        raise


def get_netex_text(xml_data: _Element, element_name: str) -> str | None:
    """
    Get text from element in NeTEx namespace
    """
    element = get_netex_element(xml_data, element_name)
    if element is not None:
        return element.text
    return None


def get_netex_int(xml_data: _Element, element_name: str) -> int | None:
    """
    Parse Element Text as Int
    """
    text = get_netex_text(xml_data, element_name)
    if text is None:
        return None
    try:
        return int(text)
    except (ValueError, TypeError):
        log.warning("Could not parse element as int", element_name=element_name)
        return None


def get_netex_bool(xml_data: _Element, element_name: str) -> bool | None:
    """
    Parse Element Text as Bool
    """
    text = get_netex_text(xml_data, element_name)
    if text is None:
        return None

    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False

    log.warning("Could not parse element as bool", element_name=element_name)
    return None


def find_required_netex_element(xml_data: _Element, element_name: str) -> _Element:
    """Find required element in NeTEx namespace"""
    element = get_netex_element(xml_data, element_name)
    if element is None:
        error_message = f"Required NeTEx element not found: {element_name}"
        log.warning(error_message)
        raise ValueError(error_message)
    return element


def parse_timestamp(elem: _Element, element_name: str) -> datetime | None:
    """
    Parse Timestamp element
    """
    text = get_netex_text(elem, element_name)
    if text is not None:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        # If the datetime is naive (no timezone info), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    return None


def parse_multilingual_string(
    elem: _Element, element_name: str
) -> MultilingualString | None:
    """Parse Description element."""
    child = get_netex_element(elem, element_name)
    if child is None:
        return None
    if child.text is None:
        return None
    return MultilingualString(
        value=child.text, lang=child.get("lang"), textIdType=child.get("textIdType")
    )


def parse_timedelta(elem: _Element, element_name: str) -> timedelta | None:
    """
    Parse Timedeltas
    """
    text = get_netex_text(elem, element_name)
    if text:
        return timedelta(seconds=float(text))
    return None


def parse_versioned_ref(elem: _Element, element_name: str) -> VersionedRef | None:
    """
    Parse element as VersionedRef.

    Some fields use version and others use versionRef
    According to the spec they are mutually exclusive
    So could just use one

    Priority:
    1. `version` attribute
    2. `versionRef` attribute
    """
    child = get_netex_element(elem, element_name) if element_name else elem
    if child is None:
        return None

    ref = child.get("ref")
    if ref is None or ref == "":
        return None

    version = child.get("version") or child.get("versionRef")

    return VersionedRef(
        version=version,
        ref=ref,
    )


def parse_from_to_date(elem: _Element) -> FromToDate:
    """
    Parse ValidBetween element containing FromDate and ToDate
    """
    from_date = parse_timestamp(elem, "FromDate")
    to_date = parse_timestamp(elem, "ToDate")

    return FromToDate(
        FromDate=from_date,
        ToDate=to_date,
    )
