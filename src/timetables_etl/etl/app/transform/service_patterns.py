"""
Make Transmodel Service Patterns
"""

from common_layer.database.models import (
    OrganisationDatasetRevision,
    TransmodelServicePattern,
)
from common_layer.xml.txc.helpers import get_stops_from_sections
from common_layer.xml.txc.models import (
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCService,
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

log = get_logger()


def get_valid_route_points(
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    atco_location_mapping: StopsLookup,
) -> list[Point]:
    """
    Get valid route points from journey pattern sections.
    Logs warnings for any stops not found in the mapping.
    """
    stops: list[str] = get_stops_from_sections(
        jp.JourneyPatternSectionRefs, journey_pattern_sections
    )
    route_points: list[Point] = []

    for stop in stops:
        if stop not in atco_location_mapping:
            log.warning(
                "Stop not found in location mapping",
                stop_id=stop,
                journey_pattern_id=jp.id,
            )
            continue
        route_points.append(atco_location_mapping[stop].shape)

    return route_points


def generate_service_pattern_geometry(
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    atco_location_mapping: StopsLookup,
) -> WKBElement | None:
    """
    Generate the Stop Linestring for a JourneyPattern.
    SRID 4326 (WGS84) which is Longitude / Latitude.

    Returns:
        WKBElement: The geometry of the journey pattern
        None: If insufficient valid stops are found to create a linestring
    """
    route_points = get_valid_route_points(
        jp, journey_pattern_sections, atco_location_mapping
    )

    if len(route_points) <= 1:
        log.warning(
            "Not enough valid stops to create service pattern",
            journey_pattern_id=jp.id,
            valid_stops_count=len(route_points),
        )
        return None

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
