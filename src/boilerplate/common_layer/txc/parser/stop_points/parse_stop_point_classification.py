"""
Parse TXC Stop Point Classification
"""

from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...models import (
    BearingStructure,
    BusStopStructure,
    MarkedPointStructure,
    OnStreetStructure,
    StopClassificationStructure,
)
from ...models.txc_stoppoint import OffStreetStructure, UnmarkedPointStructure
from ...models.txc_types import (
    STOP_CLASSIFICATION_STOP_TYPE_MAPPING,
    TIMING_STATUS_MAPPING,
    BusStopTypeT,
    CompassPointT,
    TimingStatusT,
    TXCStopTypeT,
)
from ..utils_tags import get_element_text
from .parse_stop_point_types import parse_bus_and_coach_structure, parse_ferry_structure

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


def parse_bus_stop_structure(bus_xml: _Element) -> BusStopStructure | None:
    """
    Parse the Bus structure within the OnStreet section.

    StopPoints -> StopPoint -> StopClassification -> OnStreet -> Bus
    """
    marked_point_xml = bus_xml.find("MarkedPoint")
    unmarked_point_xml = bus_xml.find("UnmarkedPoint")

    marked_point = (
        parse_marked_point_structure(marked_point_xml)
        if marked_point_xml is not None
        else None
    )

    unmarked_point = (
        parse_unmarked_point_structure(unmarked_point_xml)
        if unmarked_point_xml is not None
        else None
    )

    bus_stop_type = get_element_text(bus_xml, "BusStopType")
    timing_status_code = get_element_text(bus_xml, "TimingStatus")

    if timing_status_code is not None:
        timing_status = TIMING_STATUS_MAPPING.get(timing_status_code)
    else:
        timing_status = None

    # Validate required fields
    if (
        bus_stop_type is None
        or timing_status is None
        or bus_stop_type not in get_args(BusStopTypeT)
        or timing_status not in get_args(TimingStatusT)
    ):
        log.warning(
            "Missing Bus Stop Structure Data Returning None",
            bus_stop_type=bus_stop_type,
            timing_status=timing_status,
            marked_point=marked_point,
            unmarked_point=unmarked_point,
        )
        return None

    # Validate that either MarkedPoint or UnmarkedPoint is present based on BusStopType
    if bus_stop_type == "marked" and marked_point is None:
        log.warning("Missing MarkedPoint for marked bus stop type")
        return None

    if bus_stop_type == "custom" and unmarked_point is None:
        log.warning("Missing UnmarkedPoint for custom bus stop type")
        return None

    return BusStopStructure(
        BusStopType=cast(BusStopTypeT, bus_stop_type),
        TimingStatus=cast(TimingStatusT, timing_status),
        MarkedPoint=marked_point,
        UnmarkedPoint=unmarked_point,
    )


def parse_on_street_structure(on_street_xml: _Element) -> OnStreetStructure | None:
    """
    Parse the OnStreet structure within the StopClassification section.

    StopPoints -> StopPoint -> StopClassification -> OnStreet
    """
    bus_xml = on_street_xml.find("Bus")
    if bus_xml is None:
        log.warning(
            "Bus XML Missing. Perhaps other implemented data",
            on_street_xml=on_street_xml,
        )
        return None

    bus = parse_bus_stop_structure(bus_xml)

    if bus:
        return OnStreetStructure(Bus=bus)
    return None


def parse_off_street_structure(off_street_xml: _Element) -> OffStreetStructure | None:
    """
    Parse the OffStreet structure within the StopClassification section.
    StopPoints -> StopPoint -> StopClassification -> OffStreet
    """
    # Try BusAndCoach
    bus_and_coach_xml = off_street_xml.find("BusAndCoach")
    if bus_and_coach_xml is not None:
        bus_and_coach = parse_bus_and_coach_structure(bus_and_coach_xml)
        if bus_and_coach:
            return OffStreetStructure(BusAndCoach=bus_and_coach)

    # Try Ferry
    ferry_xml = off_street_xml.find("Ferry")
    if ferry_xml is not None:
        ferry = parse_ferry_structure(ferry_xml)
        if ferry:
            return OffStreetStructure(Ferry=ferry)

    log.warning(
        "No supported OffStreet structure found",
        off_street_xml=off_street_xml,
    )
    return None


def parse_stop_classification_structure(
    stop_classification_xml: _Element,
) -> StopClassificationStructure | None:
    """
    StopPoints -> StopPoint -> StopClassification
    """
    stop_type = get_element_text(stop_classification_xml, "StopType")
    if not stop_type:
        log.warning("Missing StopType")
        return None

    # Map the stop type if it's in our mapping
    mapped_stop_type = STOP_CLASSIFICATION_STOP_TYPE_MAPPING.get(stop_type, stop_type)

    # Now validate against TXCStopTypeT
    if mapped_stop_type not in get_args(TXCStopTypeT):
        log.warning(
            "Invalid StopType", stop_type=stop_type, mapped_stop_type=mapped_stop_type
        )
        return None

    # Try parsing OnStreet first
    on_street_xml = stop_classification_xml.find("OnStreet")
    if on_street_xml is not None:
        on_street = parse_on_street_structure(on_street_xml)
        if on_street:
            return StopClassificationStructure(
                StopType=cast(TXCStopTypeT, mapped_stop_type),
                OnStreet=on_street,
                OffStreet=None,
            )

    # If no OnStreet, try OffStreet
    off_street_xml = stop_classification_xml.find("OffStreet")
    if off_street_xml is not None:
        off_street = parse_off_street_structure(off_street_xml)
        if off_street:
            return StopClassificationStructure(
                StopType=cast(TXCStopTypeT, mapped_stop_type),
                OffStreet=off_street,
                OnStreet=None,
            )

    log.warning(
        "Missing both OnStreet and OffStreet sections",
        stop_classification_xml=stop_classification_xml,
    )
    return None
