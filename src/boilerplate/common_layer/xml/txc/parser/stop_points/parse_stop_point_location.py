"""
Location Parsing
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_element_text
from ...models import LocationStructure, PlaceStructure

log = get_logger()


def parse_location_structure(location_xml: _Element) -> LocationStructure:
    """
    StopPoints -> StopPoint -> Place -> Location
    """
    translation_xml = location_xml.find("Translation")
    if translation_xml is not None:
        return LocationStructure(
            Longitude=get_element_text(translation_xml, "Longitude"),
            Latitude=get_element_text(translation_xml, "Latitude"),
            Easting=get_element_text(translation_xml, "Easting"),
            Northing=get_element_text(translation_xml, "Northing"),
        )
    return LocationStructure(
        Longitude=get_element_text(location_xml, "Longitude"),
        Latitude=get_element_text(location_xml, "Latitude"),
        Easting=get_element_text(location_xml, "Easting"),
        Northing=get_element_text(location_xml, "Northing"),
    )


def parse_place_structure(place_xml: _Element) -> PlaceStructure | None:
    """
    StopPoints -> StopPoint -> Place
    """
    location_xml = place_xml.find("Location")
    location = (
        parse_location_structure(location_xml) if location_xml is not None else None
    )
    locality_ref = get_element_text(place_xml, "NptgLocalityRef")
    if not locality_ref or not location:
        log.warning(
            "Missing Place Structure Required Field",
            locality_ref=locality_ref,
            location=location,
        )
        return None
    return PlaceStructure(
        NptgLocalityRef=locality_ref,
        LocalityName=get_element_text(place_xml, "LocalityName"),
        Location=location,
    )
