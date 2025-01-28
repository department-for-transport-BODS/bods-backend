"""
Stop Point Types
"""

from typing import cast, get_args

from common_layer.txc.parser.utils_tags import get_element_text
from lxml.etree import _Element  # type: ignore

from ...models import (
    AirStopClassificationStructure,
    BayStructure,
    BusAndCoachStationStructure,
    FerryStopClassificationStructure,
    MetroStopClassificationStructure,
    RailStopClassificationStructure,
)
from ...models.txc_types import TIMING_STATUS_MAPPING, TimingStatusT


def parse_bay_structure(bay_xml: _Element) -> BayStructure:
    """
    Parse the Bay structure within BusAndCoach section.
    StopPoints -> StopPoint -> StopClassification -> OffStreet -> BusAndCoach -> Bay
    """
    timing_status_code = get_element_text(bay_xml, "TimingStatus")
    if timing_status_code:
        timing_status = TIMING_STATUS_MAPPING.get(timing_status_code)
        if timing_status and timing_status in get_args(TimingStatusT):
            return BayStructure(TimingStatus=cast(TimingStatusT, timing_status))

    return BayStructure()


def parse_bus_and_coach_structure(
    bus_and_coach_xml: _Element,
) -> BusAndCoachStationStructure | None:
    """
    Parse the BusAndCoach structure within the OffStreet section.
    StopPoints -> StopPoint -> StopClassification -> OffStreet -> BusAndCoach
    """
    bay: BayStructure | None = None
    bay_xml = bus_and_coach_xml.find("Bay")
    if bay_xml is not None:
        bay = parse_bay_structure(bay_xml)

    varibay: BayStructure | None = None
    varibay_xml = bus_and_coach_xml.find("VariableBay")
    if varibay_xml is not None:
        varibay = parse_bay_structure(varibay_xml)

    entrance: bool = bus_and_coach_xml.find("Entrance") is not None
    access_area: bool = bus_and_coach_xml.find("AccessArea") is not None

    if not any([bay, varibay, entrance, access_area]):
        return None

    return BusAndCoachStationStructure(
        Bay=bay, VariableBay=varibay, Entrance=entrance, AccessArea=access_area
    )


def parse_ferry_structure(
    ferry_xml: _Element,
) -> FerryStopClassificationStructure | None:
    """
    Parse the Ferry structure within the OffStreet section.
    StopPoints -> StopPoint -> StopClassification -> OffStreet -> Ferry
    """
    entrance: bool = ferry_xml.find("Entrance") is not None
    access_area: bool = ferry_xml.find("AccessArea") is not None
    berth: bool = ferry_xml.find("Berth") is not None

    if not any([entrance, access_area, berth]):
        return None

    return FerryStopClassificationStructure(
        Entrance=entrance, AccessArea=access_area, Berth=berth
    )


def parse_rail_structure(
    rail_xml: _Element,
) -> RailStopClassificationStructure | None:
    """
    Parse the Rail structure within the OffStreet section.
    StopPoints -> StopPoint -> StopClassification -> OffStreet -> Rail
    """
    entrance: bool = rail_xml.find("Entrance") is not None
    access_area: bool = rail_xml.find("AccessArea") is not None
    platform: bool = rail_xml.find("Platform") is not None

    if not any([entrance, access_area, platform]):
        return None

    return RailStopClassificationStructure(
        Entrance=entrance, AccessArea=access_area, Platform=platform
    )


def parse_metro_structure(
    metro_xml: _Element,
) -> MetroStopClassificationStructure | None:
    """Parse the Metro structure within the OffStreet section."""
    entrance_xml = metro_xml.find("Entrance")
    access_area_xml = metro_xml.find("AccessArea")
    platform_xml = metro_xml.find("Platform")

    entrance = entrance_xml is not None
    access_area = access_area_xml is not None
    platform = platform_xml is not None

    if not (entrance or access_area or platform):
        return None

    return MetroStopClassificationStructure(
        Entrance=entrance, Platform=platform, AccessArea=access_area
    )


def parse_air_structure(
    metro_xml: _Element,
) -> AirStopClassificationStructure | None:
    """Parse the Air structure within the OffStreet section."""
    entrance_xml = metro_xml.find("Entrance")
    access_area_xml = metro_xml.find("AccessArea")

    entrance = entrance_xml is not None
    access_area = access_area_xml is not None

    if not (entrance or access_area):
        return None

    return AirStopClassificationStructure(Entrance=entrance, AccessArea=access_area)
