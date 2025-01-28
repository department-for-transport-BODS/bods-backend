"""
Stop Point Types
"""

from typing import cast, get_args

from common_layer.txc.parser.utils_tags import get_element_text
from lxml.etree import _Element  # type: ignore

from ...models import (
    BayStructure,
    BusAndCoachStationStructure,
    FerryStopClassificationStructure,
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
    bay_xml = bus_and_coach_xml.find("Bay")
    if bay_xml is not None:
        bay = parse_bay_structure(bay_xml)
        return BusAndCoachStationStructure(Bay=bay)
    return None


def parse_ferry_structure(
    ferry_xml: _Element,
) -> FerryStopClassificationStructure | None:
    """
    Parse the Ferry structure within the OffStreet section.
    StopPoints -> StopPoint -> StopClassification -> OffStreet -> Ferry
    """
    entrance_xml = ferry_xml.find("Entrance")
    if entrance_xml is not None:
        return FerryStopClassificationStructure(Entrance=True)
    return None
