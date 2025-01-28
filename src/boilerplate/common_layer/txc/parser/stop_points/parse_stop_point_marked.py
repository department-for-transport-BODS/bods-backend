"""
Marked Point / Bearings
"""

from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...models import BearingStructure, MarkedPointStructure, UnmarkedPointStructure
from ...models.txc_types import CompassPointT
from ..utils_tags import get_element_text

log = get_logger()


def parse_bearing_structure(bearing_xml: _Element) -> BearingStructure | None:
    """
    StopPoints -> StopPoint -> StopClassification -> OnStreet -> Bus -> MarkedPoint -> Bearing
    """
    compass_point = get_element_text(bearing_xml, "CompassPoint")
    if compass_point and compass_point in get_args(CompassPointT):
        return BearingStructure(CompassPoint=cast(CompassPointT, compass_point))
    log.warning("Incorrect Compass Point")
    return None


def parse_unmarked_point_structure(
    unmarked_point_xml: _Element,
) -> UnmarkedPointStructure | None:
    """
    StopPoints -> StopPoint -> StopClassification -> OnStreet -> Bus -> UnmarkedPoint
    """
    bearing_xml = unmarked_point_xml.find("Bearing")
    if bearing_xml is None:
        return None
    bearing = parse_bearing_structure(bearing_xml)
    return UnmarkedPointStructure(Bearing=bearing) if bearing else None


def parse_marked_point_structure(
    marked_point_xml: _Element,
) -> MarkedPointStructure | None:
    """
    StopPoints -> StopPoint -> StopClassification -> OnStreet -> Bus -> MarkedPoint
    """
    bearing_xml = marked_point_xml.find("Bearing")
    if bearing_xml is None:
        return None
    bearing = parse_bearing_structure(bearing_xml)
    return MarkedPointStructure(Bearing=bearing) if bearing else None
