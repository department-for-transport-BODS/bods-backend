"""
Service Pattern Geometry Calculation
"""

from common_layer.database.models.model_naptan import NaptanStopPoint
from common_layer.xml.txc.helpers import get_stops_from_sections
from common_layer.xml.txc.models import TXCJourneyPattern, TXCJourneyPatternSection
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely import Point
from shapely.geometry import LineString
from structlog.stdlib import get_logger

from ..helpers import NonExistentNaptanStop, StopsLookup

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
    stops_refs: list[str] = get_stops_from_sections(
        jp.JourneyPatternSectionRefs, journey_pattern_sections
    )
    route_points: list[Point] = []

    for stop_ref in stops_refs:
        if not stop_ref in atco_location_mapping:
            msg = "Stop referenced in JourneyPatternSections not found in stop map"
            log.error(msg, stop_id=stop_ref)
            raise ValueError(msg)

        stop_data = atco_location_mapping[stop_ref]
        if isinstance(stop_data, NonExistentNaptanStop):
            log.warning(
                "Skipping NonExistentNaptanStop",
                stop_id=stop_ref,
                journey_pattern_id=jp.id,
            )
            continue
        route_points.append(stop_data.shape)

    return route_points


def get_valid_route_points_from_list(
    stop_points: list[NaptanStopPoint],
) -> list[Point]:
    """
    Get valid route points from a list of NaptanStopPoint objects.

    """
    route_points: list[Point] = []

    for stop in stop_points:
        # Skip NonExistentNaptanStop if somehow passed in the list
        if isinstance(stop, NonExistentNaptanStop):
            log.warning(
                "Skipping NonExistentNaptanStop",
                stop_id=stop.atco_code,
            )
            continue

        # Add the shape of valid stops to route_points
        route_points.append(stop.shape)

    if len(route_points) <= 1:
        log.warning(
            "Not enough valid stops to create service pattern",
            valid_stops_count=len(route_points),
        )

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


def generate_service_pattern_geometry_from_list(
    stop_points: list[NaptanStopPoint],
) -> WKBElement | None:
    """
    Generate the Stop Linestring from a list of NaptanStopPoint objects.
    SRID 4326 (WGS84) which is Longitude / Latitude.

    Returns:
        WKBElement: The geometry of the service pattern
        None: If insufficient valid stops are found to create a linestring
    """
    route_points = get_valid_route_points_from_list(stop_points)

    if len(route_points) <= 1:
        log.warning(
            "Not enough valid stops to create service pattern",
            valid_stops_count=len(route_points),
        )
        return None

    return from_shape(LineString(route_points), srid=4326)
