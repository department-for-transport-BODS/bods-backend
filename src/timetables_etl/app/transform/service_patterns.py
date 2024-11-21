"""
Make Transmodel Service Patterns
"""

from dataclasses import dataclass
from uuid import uuid4

from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely import Point
from shapely.geometry import LineString
from structlog.stdlib import get_logger

from timetables_etl.app.database.models.model_naptan import NaptanStopPoint
from timetables_etl.app.database.models.model_organisation import (
    OrganisationDatasetRevision,
)
from timetables_etl.app.database.models.model_transmodel import TransmodelServicePattern
from timetables_etl.app.txc.helpers.jps import (
    get_jps_by_id,
    get_stops_from_journey_pattern_section,
)
from timetables_etl.app.txc.models.txc_journey_pattern import TXCJourneyPatternSection
from timetables_etl.app.txc.models.txc_service import TXCJourneyPattern, TXCService

log = get_logger()


@dataclass(frozen=True)
class PatternMetadata:
    """Metadata about a service pattern's origin and destination"""

    origin: str
    destination: str
    description: str
    line_name: str

    @classmethod
    def unknown(cls, line_name: str) -> "PatternMetadata":
        """Create a metadata object for unknown origin/destination"""
        return cls(
            origin="unknown",
            destination="unknown",
            description="unknown",
            line_name=line_name,
        )


def extract_pattern_metadata(
    service: TXCService, jp: TXCJourneyPattern
) -> PatternMetadata:
    """
    Extract pattern metadata from service and journey pattern
    """
    if len(service.Lines) == 0:
        log.warning("No Lines in TXC Service")
        return PatternMetadata.unknown("unknown")

    line = service.Lines[0]
    if len(service.Lines) > 1:
        log.warning("More than 1 Line using first for Service Patterns")

    description = (
        line.InboundDescription
        if jp.Direction == "inbound"
        else line.OutboundDescription
    )
    if description:
        return PatternMetadata(
            origin=description.Origin,
            destination=description.Destination,
            description=description.Description,
            line_name=line.LineName,
        )

    log.warning(
        "Direction or Inbound/Outbound Direction Missing", direction=jp.Direction
    )
    return PatternMetadata.unknown(line.LineName)


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
    atco_location_mapping: dict[str, NaptanStopPoint],
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
            route_points.append(atco_location_mapping[stop].shape)
    line = LineString(route_points)
    return from_shape(line, srid=4326)


def create_service_pattern(
    service: TXCService,
    jp: TXCJourneyPattern,
    revision: OrganisationDatasetRevision,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    stop_mapping: dict[str, NaptanStopPoint],
) -> TransmodelServicePattern:
    """
    Create a single TransmodelServicePattern from a TXC journey pattern
    """
    metadata = extract_pattern_metadata(service, jp)

    pattern = TransmodelServicePattern(
        service_pattern_id=make_service_pattern_id(service, jp),
        origin=metadata.origin,
        destination=metadata.destination,
        description=metadata.description,
        revision_id=revision.id,
        line_name=metadata.line_name,
        geom=generate_service_pattern_geometry(
            jp, journey_pattern_sections, stop_mapping
        ),
    )

    log.info(
        "Created service pattern",
        pattern_id=pattern.service_pattern_id,
    )
    return pattern
