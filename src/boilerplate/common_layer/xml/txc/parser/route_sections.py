"""
Parse Route Sections XML into Pydantic Models
"""

from common_layer.utils_location import osgrid_to_lonlat
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import (
    find_section,
    get_element_int,
    get_element_text,
    parse_creation_datetime,
    parse_modification,
    parse_modification_datetime,
    parse_revision_number,
)
from ..models import TXCLocation, TXCMapping, TXCRouteLink, TXCRouteSection, TXCTrack

log = get_logger()


def get_lon_lat_from_location(
    element: _Element,
) -> tuple[str, str] | tuple[None, None]:
    """
    Get (lon, lat) from given location element
    """
    longitude = get_element_text(element, "Longitude")
    latitude = get_element_text(element, "Latitude")
    if longitude and latitude:
        return longitude, latitude

    easting = get_element_text(element, "Easting")
    northing = get_element_text(element, "Northing")
    if easting and northing:
        lon, lat = osgrid_to_lonlat(float(easting), float(northing))
        return str(lon), str(lat)

    return None, None


def parse_location(location_xml: _Element) -> TXCLocation | None:
    """
    Create TXC Location from XML
    """
    location_id = location_xml.get("id")
    if not location_id:
        return None

    lon, lat = None, None
    translation = location_xml.find("Translation", None)
    if translation:Check warningCheck warning: The behavior of this method will change in future versions. Use specific 'len(elem)' or 'elem is not None' test instead.pytest / pytestView detailsCode has alerts. Press enter to view.
        lon, lat = get_lon_lat_from_location(translation)
    else:
        lon, lat = get_lon_lat_from_location(location_xml)

    if lon and lat:
        return TXCLocation(id=location_id, Longitude=lon, Latitude=lat)

    return None


def parse_locations(track_xml: _Element) -> list[TXCLocation] | None:
    """
    Create Locations list
    """
    if track_xml.tag != "Track":
        return None
    locations: list[TXCLocation] = []
    location_xmls = track_xml.findall("Mapping/Location")
    if location_xmls:
        for location_xml in location_xmls:
            location = parse_location(location_xml)
            if location:
                locations.append(location)
        return locations
    return None


def parse_track(route_link_xml: _Element) -> TXCTrack | None:
    """
    Create Track
    """
    track_xml = route_link_xml.find("Track")
    if track_xml is not None:
        locations = parse_locations(track_xml)
        if locations:
            mapping = TXCMapping(Location=locations)
            return TXCTrack(Mapping=mapping)
    return None


def parse_route_link(
    route_link_xml: _Element, parse_track_data: bool
) -> TXCRouteLink | None:
    """
    Make a rouse link from XML data
    """
    route_link_id = route_link_xml.get("id")
    if not route_link_id:
        log.warning("RouteLink missing required id attribute. Skipping.")
        return None

    from_stop_point_ref = get_element_text(route_link_xml, "From/StopPointRef")
    to_stop_point_ref = get_element_text(route_link_xml, "To/StopPointRef")
    if not from_stop_point_ref or not to_stop_point_ref:
        log.warning(
            "RouteLink missing required From/To StopPointRef. Skipping.",
            RouteLink=route_link_id,
        )
        return None

    creation_datetime = parse_creation_datetime(route_link_xml)
    modification_datetime = parse_modification_datetime(route_link_xml)
    modification = parse_modification(route_link_xml)
    revision_number = parse_revision_number(route_link_xml)
    distance = get_element_int(route_link_xml, "Distance")

    track = parse_track(route_link_xml) if parse_track_data else None

    return TXCRouteLink(
        id=route_link_id,
        From=from_stop_point_ref,
        To=to_stop_point_ref,
        CreationDateTime=creation_datetime,
        ModificationDateTime=modification_datetime,
        Modification=modification,
        RevisionNumber=revision_number,
        Distance=distance,
        Track=track,
    )


def parse_route_links(
    route_section_xml: _Element, parse_track_data: bool
) -> list[TXCRouteLink]:
    """
    Generate list of route links
    """
    route_links: list[TXCRouteLink] = []
    route_link_xmls = route_section_xml.findall("RouteLink")

    for route_link_xml in route_link_xmls:
        route_link = parse_route_link(route_link_xml, parse_track_data)
        if route_link:
            route_links.append(route_link)

    return route_links


def parse_route_section(
    route_section_xml: _Element, parse_track_data: bool
) -> TXCRouteSection | None:
    """
    Parse each Route Section into a Pydantic Model
    """
    route_section_id = route_section_xml.get("id")
    if not route_section_id:
        log.warning("RouteSection missing required id attribute. Skipping.")
        return None

    creation_datetime = parse_creation_datetime(route_section_xml)
    modification_datetime = parse_modification_datetime(route_section_xml)
    route_links = parse_route_links(route_section_xml, parse_track_data)

    return TXCRouteSection(
        id=route_section_id,
        CreationDateTime=creation_datetime,
        ModificationDateTime=modification_datetime,
        RouteLink=route_links,
    )


def parse_route_sections(
    xml_data: _Element, parse_track_data: bool
) -> list[TXCRouteSection]:
    """
    Convert RouteSections XML into Pydantic Models
    """
    try:
        section = find_section(xml_data, "RouteSections")
    except ValueError:
        return []

    route_sections: list[TXCRouteSection] = []
    route_section_xmls = section.findall("RouteSection")

    for route_section_xml in route_section_xmls:
        generated_route_section = parse_route_section(
            route_section_xml, parse_track_data
        )
        if generated_route_section:
            route_sections.append(generated_route_section)
    log.info("Parsed Route Sections", count=len(route_sections))
    return route_sections
