"""
Make Transmodel Service Patterns
"""

from uuid import uuid4

from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely import Point
from shapely.geometry import LineString
from structlog.stdlib import get_logger

from timetables_etl.app.database.models.model_organisation import (
    OrganisationDatasetRevision,
)
from timetables_etl.app.database.models.model_transmodel import TransmodelServicePattern
from timetables_etl.app.txc.helpers.jps import (
    get_jps_by_id,
    get_stops_from_journey_pattern_section,
)
from timetables_etl.app.txc.models.txc_data import TXCData
from timetables_etl.app.txc.models.txc_journey_pattern import TXCJourneyPatternSection
from timetables_etl.app.txc.models.txc_service import TXCJourneyPattern, TXCService

log = get_logger()


def make_service_pattern_id(service: TXCService, jp: TXCJourneyPattern):
    """
    Generate a Unique Service Pattern ID to be used
    """
    return f"{service.ServiceCode}-{jp.id}-{uuid4()}"


def get_jp_origin_destination(
    service: TXCService, jp: TXCJourneyPattern
) -> tuple[str, str, str]:
    """
    Get the Origin, Destination and Description for a Journey Pattern
    """
    if len(service.Lines) > 1:
        log.warning("More than 1 Line using first for Service Patterns")
    if len(service.Lines) == 0:
        log.warning("No Lines in TXC Service")
    line = service.Lines[0]
    if jp.Direction == "inbound":
        if line.InboundDescription:
            return (
                line.InboundDescription.Origin,
                line.InboundDescription.Destination,
                line.InboundDescription.Description,
            )
    if jp.Direction == "outbound":
        if line.OutboundDescription:
            return (
                line.OutboundDescription.Origin,
                line.OutboundDescription.Destination,
                line.OutboundDescription.Description,
            )
    log.warning(
        "Direction or Inbound/Outbound Direction Missing", direction=jp.Direction
    )
    return "unknown", "unknown", "unknown"


def generate_service_pattern_geometry(
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    atco_location_mapping: dict[str, Point],
) -> WKBElement:
    """
    Generate the Stop Linestring for a JourneyPattern
    SRID 4326 (WGS84) which is Longitude / Latitude
    """
    route_points: list[Point] = []
    for jps_id in jp.JourneyPatternSectionRefs:
        jps = get_jps_by_id(jps_id, journey_pattern_sections)
        stops = get_stops_from_journey_pattern_section(jps)
        for stop in stops:
            route_points.append(atco_location_mapping[stop])
    line = LineString(route_points)
    return from_shape(line, srid=4326)


def make_transmodels_service_patterns(
    txc: TXCData,
    revision: OrganisationDatasetRevision,
    atco_location_mapping: dict[str, Point],
) -> list[TransmodelServicePattern]:
    """
    Transmodel Service Patterns contain the points for particular service
    """

    service_patterns: list[TransmodelServicePattern] = []
    for service in txc.Services:
        if service.StandardService:
            for jp in service.StandardService.JourneyPattern:
                origin, destination, description = get_jp_origin_destination(
                    service, jp
                )
                service_patterns.append(
                    TransmodelServicePattern(
                        service_pattern_id=make_service_pattern_id(service, jp),
                        origin=origin,
                        destination=destination,
                        description=description,
                        revision_id=revision.id,
                        line_name=service.Lines[0].LineName,
                        geom=generate_service_pattern_geometry(
                            jp, txc.JourneyPatternSections, atco_location_mapping
                        ),
                    )
                )

    return service_patterns
