"""
Parse OnStreet XML
"""

from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_element_text
from ...models import (
    TIMING_STATUS_MAPPING,
    BusStopStructure,
    BusStopTypeT,
    OnStreetStructure,
    TaxiStopClassificationStructure,
    TimingStatusT,
)
from .parse_stop_point_marked import (
    parse_marked_point_structure,
    parse_unmarked_point_structure,
)

log = get_logger()


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

    return BusStopStructure(
        BusStopType=cast(BusStopTypeT, bus_stop_type),
        TimingStatus=cast(TimingStatusT, timing_status),
        MarkedPoint=marked_point,
        UnmarkedPoint=unmarked_point,
    )


def parse_taxi_structure(taxi_xml: _Element) -> TaxiStopClassificationStructure | None:
    """
    Parse Taxi OnStreet Structure
    """
    taxi_rank: _Element | None = taxi_xml.find("TaxiRank")
    shared_taxi_rank: _Element | None = taxi_xml.find("SharedTaxiRank")

    taxi_rank_bool: bool = taxi_rank is not None
    shared_taxi_rank_bool: bool = shared_taxi_rank is not None

    if not (taxi_rank_bool or shared_taxi_rank_bool):
        return None

    return TaxiStopClassificationStructure(
        TaxiRank=taxi_rank_bool, SharedTaxiRank=shared_taxi_rank_bool
    )


def parse_on_street_structure(on_street_xml: _Element) -> OnStreetStructure | None:
    """
    Parse the OnStreet structure within the StopClassification section.

    StopPoints -> StopPoint -> StopClassification -> OnStreet
    """
    bus_xml = on_street_xml.find("Bus")
    if bus_xml is not None:
        bus = parse_bus_stop_structure(bus_xml)
        if bus:
            return OnStreetStructure(Bus=bus)

    taxi_xml = on_street_xml.find("Taxi")
    if taxi_xml is not None:
        taxi = parse_taxi_structure(taxi_xml)
        if taxi:
            return OnStreetStructure(Taxi=taxi)

    log.warning(
        "Missing OnStreet Data, perhaps unimplemetned",
        on_street_xml=on_street_xml,
    )
    return None
