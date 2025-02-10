"""
Parse Routes from TXC
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import (
    find_section,
    get_element_text,
    parse_creation_datetime,
    parse_modification,
    parse_modification_datetime,
    parse_revision_number,
)
from ..models import TXCRoute, TXCRouteSection

log = get_logger()


def gather_route_sections(route_xml: _Element, route_sections: list[TXCRouteSection]):
    """
    Route Sections models uses list of route section model instead of refs to ease conversion
    """
    route_sections_dict: dict[str, TXCRouteSection] = {}
    for route_section in route_sections:
        route_sections_dict[route_section.id] = route_section

    route_section_refs: list[TXCRouteSection] = []
    for route_section_ref_xml in route_xml.findall("RouteSectionRef"):
        route_section_ref = route_section_ref_xml.text
        if route_section_ref in route_sections_dict:
            route_section_refs.append(route_sections_dict[route_section_ref])
    return route_section_refs


def parse_routes(
    xml_data: _Element, route_sections: list[TXCRouteSection]
) -> list[TXCRoute]:
    """
    Routes
    """
    try:
        section = find_section(xml_data, "Routes")
    except ValueError:
        log.warning("No Routes Found")
        return []

    routes: list[TXCRoute] = []
    for route_xml in section.findall("Route"):
        route_id = route_xml.get("id")
        if not route_id:
            log.warning("Route missing required id attribute. Skipping.")
            continue

        creation_datetime = parse_creation_datetime(route_xml)
        modification_datetime = parse_modification_datetime(route_xml)
        modification = parse_modification(route_xml)
        revision_number = parse_revision_number(route_xml)
        private_code = get_element_text(route_xml, "PrivateCode")
        description = get_element_text(route_xml, "Description")
        route_section_refs = gather_route_sections(route_xml, route_sections)

        if not description:
            log.warning("Missing Route Description", route_id=route_id)
            description = "MISSING ROUTE DESCRIPTION"

        routes.append(
            TXCRoute(
                id=route_id,
                CreationDateTime=creation_datetime,
                ModificationDateTime=modification_datetime,
                Modification=modification,
                RevisionNumber=revision_number,
                PrivateCode=private_code,
                Description=description,
                RouteSectionRef=route_section_refs,
            )
        )
    log.info("Parsed Routes", count=len(routes))
    return routes
