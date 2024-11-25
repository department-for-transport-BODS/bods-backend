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

from timetables_etl.etl.app.transform.utils_stops import get_first_last_stops
from timetables_etl.etl.app.txc.models.txc_service import TXCLine

from ..database.models import (
    NaptanStopPoint,
    OrganisationDatasetRevision,
    TransmodelServicePattern,
)
from ..txc.helpers.jps import get_stops_from_sections
from ..txc.models import TXCJourneyPattern, TXCJourneyPatternSection, TXCService

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


@dataclass(frozen=True)
class LineDescription:
    """Wrapper for line description data"""

    origin: str | None
    destination: str | None
    description: str


def get_line_description(line: TXCLine, direction: str) -> LineDescription | None:
    """
    Extract relevant direction description from line
    """
    description = (
        line.InboundDescription if direction == "inbound" else line.OutboundDescription
    )
    if not description:
        return None
    return LineDescription(
        origin=description.Origin,
        destination=description.Destination,
        description=description.Description,
    )


def extract_pattern_metadata(
    service: TXCService,
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    stop_mapping: dict[str, NaptanStopPoint],
) -> PatternMetadata:
    """
    Extract pattern metadata with priority:
    1. Line description data if available
    2. First/last stop names with generated description
    3. Unknown pattern as fallback
    """
    first_stop, last_stop = get_first_last_stops(
        jp, journey_pattern_sections, stop_mapping
    )

    if not service.Lines:
        log.warning("No Lines in TXC Service")
        return PatternMetadata(
            origin=first_stop,
            destination=last_stop,
            description=f"{first_stop} - {last_stop}",
            line_name="unknown",
        )

    line = service.Lines[0]
    if len(service.Lines) > 1:
        log.warning("More than 1 Line using first for Service Patterns")

    line_desc = get_line_description(line, jp.Direction)

    if line_desc and line_desc.origin and line_desc.destination:
        return PatternMetadata(
            origin=line_desc.origin,
            destination=line_desc.destination,
            description=line_desc.description,
            line_name=line.LineName,
        )

    if not first_stop and not last_stop:
        return PatternMetadata.unknown(line.LineName)

    return PatternMetadata(
        origin=first_stop,
        destination=last_stop,
        description=f"{first_stop} - {last_stop}",
        line_name=line.LineName,
    )


def make_service_pattern_id(service: TXCService, jp: TXCJourneyPattern):
    """
    Generate a Unique Service Pattern ID to be used
    """
    return f"{service.ServiceCode}-{jp.id}-{uuid4()}"


def generate_service_pattern_geometry(
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    atco_location_mapping: dict[str, NaptanStopPoint],
) -> WKBElement:
    """
    Generate the Stop Linestring for a JourneyPattern
    SRID 4326 (WGS84) which is Longitude / Latitude
    """
    stops: list[str] = get_stops_from_sections(
        jp.JourneyPatternSectionRefs, journey_pattern_sections
    )
    route_points: list[Point] = [atco_location_mapping[stop].shape for stop in stops]
    return from_shape(LineString(route_points), srid=4326)


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
    metadata = extract_pattern_metadata(
        service, jp, journey_pattern_sections, stop_mapping
    )

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
