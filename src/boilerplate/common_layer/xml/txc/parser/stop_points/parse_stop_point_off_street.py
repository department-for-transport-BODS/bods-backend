"""
Parse OffStreet StopPoints Classification
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...models import OffStreetStructure
from .parse_stop_point_types import (
    parse_air_structure,
    parse_bus_and_coach_structure,
    parse_ferry_structure,
    parse_metro_structure,
    parse_rail_structure,
)

log = get_logger()


def parse_off_street_structure(off_street_xml: _Element) -> OffStreetStructure | None:
    """Parse the OffStreet structure within the StopClassification section."""
    bus_and_coach_xml = off_street_xml.find("BusAndCoach")
    if bus_and_coach_xml is not None:
        bus_and_coach = parse_bus_and_coach_structure(bus_and_coach_xml)
        if bus_and_coach:
            return OffStreetStructure(BusAndCoach=bus_and_coach)

    ferry_xml = off_street_xml.find("Ferry")
    if ferry_xml is not None:
        ferry = parse_ferry_structure(ferry_xml)
        if ferry:
            return OffStreetStructure(Ferry=ferry)

    rail_xml = off_street_xml.find("Rail")
    if rail_xml is not None:
        rail = parse_rail_structure(rail_xml)
        if rail:
            return OffStreetStructure(Rail=rail)

    metro_xml = off_street_xml.find("Metro")
    if metro_xml is not None:
        metro = parse_metro_structure(metro_xml)
        if metro:
            return OffStreetStructure(Metro=metro)

    air_xml = off_street_xml.find("Air")
    if air_xml is not None:
        air = parse_air_structure(air_xml)
        if air:
            return OffStreetStructure(Air=air)

    log.warning("No supported OffStreet structure found", off_street_xml=off_street_xml)
    return None
