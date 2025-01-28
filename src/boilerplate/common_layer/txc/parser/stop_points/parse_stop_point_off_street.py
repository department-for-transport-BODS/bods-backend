"""
Parse OffStreet StopPoints Classification
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...models.txc_stoppoint import OffStreetStructure
from .parse_stop_point_types import (
    parse_bus_and_coach_structure,
    parse_ferry_structure,
    parse_rail_structure,
)

log = get_logger()


def parse_off_street_structure(off_street_xml: _Element) -> OffStreetStructure | None:
    """Parse the OffStreet structure within the StopClassification section."""
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

    # Try Rail
    rail_xml = off_street_xml.find("Rail")
    if rail_xml is not None:
        rail = parse_rail_structure(rail_xml)
        if rail:
            return OffStreetStructure(Rail=rail)

    log.warning("No supported OffStreet structure found", off_street_xml=off_street_xml)
    return None
