"""
Make Transmodel Service Patterns
"""

from common_layer.database.models import (
    OrganisationDatasetRevision,
    TransmodelServicePattern,
)
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely import Point
from shapely.geometry import LineString
from structlog.stdlib import get_logger

from ..helpers import StopsLookup
from ..transform.service_pattern_metadata import (
    extract_pattern_metadata,
    make_service_pattern_id,
)
from ..txc.helpers.jps import get_stops_from_sections
from ..txc.models import TXCJourneyPattern, TXCJourneyPatternSection, TXCService

log = get_logger()


def generate_service_pattern_geometry(
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    atco_location_mapping: StopsLookup,
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
    stop_mapping: StopsLookup,
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
