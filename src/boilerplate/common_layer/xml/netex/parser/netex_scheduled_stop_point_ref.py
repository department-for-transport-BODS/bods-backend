"""
Special Parising of ScheduledStopPointRef
"""

from lxml.etree import _Element
from structlog.stdlib import get_logger

from ..models import ScheduledStopPointReference
from .netex_constants import NETEX_NS
from .netex_utility import get_netex_element

log = get_logger()


def parse_scheduled_stop_point_ref(
    elem: _Element,
) -> ScheduledStopPointReference | None:
    """
    Parse a single ScheduledStopPointRef element.
    """
    if elem.tag == f"{{{NETEX_NS}}}ScheduledStopPointRef":
        scheduled_stop_point_ref = elem
    else:
        scheduled_stop_point_ref = get_netex_element(elem, "ScheduledStopPointRef")
        if scheduled_stop_point_ref is None:
            return None

    ref = scheduled_stop_point_ref.get("ref")
    if ref is None:
        log.warning("Missing Ref")
        return None
    version = scheduled_stop_point_ref.get("version")
    name = scheduled_stop_point_ref.text

    return ScheduledStopPointReference(ref=ref, version=version, Name=name)


def parse_scheduled_stop_point_refs(
    elem: _Element,
) -> list[ScheduledStopPointReference]:
    """
    Parse multiple ScheduledStopPointRef elements.
    """
    scheduled_stop_point_refs: list[ScheduledStopPointReference] = []

    if elem.tag == f"{{{NETEX_NS}}}ScheduledStopPointRef":
        ref = parse_scheduled_stop_point_ref(elem)
        if ref is not None:
            scheduled_stop_point_refs.append(ref)
    else:
        # Otherwise process all children
        for child in elem:
            ref = parse_scheduled_stop_point_ref(child)
            if ref is not None:
                scheduled_stop_point_refs.append(ref)

    return scheduled_stop_point_refs
