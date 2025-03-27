"""
Service Pattern Geometry Calculation
"""

from typing import Sequence

from common_layer.database.models import NaptanStopPoint
from common_layer.xml.txc.helpers import get_stops_from_sections
from common_layer.xml.txc.models import (
    LocationStructure,
    TXCJourneyPattern,
    TXCJourneyPatternSection,
)
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape  # type: ignore
from shapely import Point
from shapely.geometry import LineString
from structlog.stdlib import get_logger

from ..helpers import FlexibleZoneLookup, NonExistentNaptanStop, StopsLookup
from .stop_points import convert_location_to_point

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


def get_valid_points_from_locations(
    locations: list[LocationStructure],
) -> list[Point]:
    """
    Return a list of Points for the given list of Locations
    """
    points: list[Point] = []
    for loc in locations:
        try:
            point = convert_location_to_point(loc)
            points.append(point)
        except ValueError as e:
            log.warning(
                "Failed to convert Location to Point",
                error=str(e),
            )
    return points


def get_valid_route_points_from_list(
    stop_points: list[NaptanStopPoint], flexible_zone_lookup: FlexibleZoneLookup | None
) -> list[Point]:
    """
    Get valid route points from a list of NaptanStopPoint objects.

    If a flexible_zone_lookup is provided, any Locations from Flexible Zones
    related to the NaptanStopPoints will be included
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

        if flexible_zone_lookup:
            flexible_locations = flexible_zone_lookup.get(stop.atco_code)
            if flexible_locations:
                route_points += get_valid_points_from_locations(flexible_locations)

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


def generate_flexible_pattern_geometry(
    stops: Sequence[str],
    stop_mapping: StopsLookup,
) -> WKBElement | None:
    """
    Generate geometry for a flexible service pattern.
    Returns None if insufficient points available to create a LineString.
    Returns:
        WKBElement containing LineString geometry if 2+ points available,
        None otherwise
    """

    route_points: list[Point] = []
    for stop in stops:
        stop_data = stop_mapping[stop]
        if not isinstance(stop_data, NonExistentNaptanStop):
            route_points.append(stop_data.shape)

    if len(route_points) < 2:
        log.warning(
            "Fewer than 2 stops so a Postgres LineString cannot be created, returning None",
            stops=stops,
        )
        return None

    return from_shape(LineString(route_points), srid=4326)


def generate_service_pattern_geometry_from_list(
    stop_points: list[NaptanStopPoint], flexible_zone_lookup: FlexibleZoneLookup | None
) -> WKBElement | None:
    """
    Generate the Stop Linestring from a list of NaptanStopPoint objects,
    including locations from flexible zones if provided.

    SRID 4326 (WGS84) which is Longitude / Latitude.

    Returns:
        WKBElement: The geometry of the service pattern
        None: If insufficient valid stops are found to create a linestring
    """
    route_points = get_valid_route_points_from_list(stop_points, flexible_zone_lookup)

    if len(route_points) <= 1:
        log.warning(
            "Not enough valid stops to create service pattern",
            valid_stops_count=len(route_points),
        )
        return None

    return from_shape(LineString(route_points), srid=4326)
