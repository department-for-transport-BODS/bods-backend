# pyright: reportUnusedImport=false
"""
Functions for loading Service Pattern Distance
"""

from math import asin, cos, radians, sin, sqrt

import pyproj
from common_layer.database import SqlDB
from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicePatternDistance,
)
from common_layer.database.repos import TransmodelServicePatternDistanceRepo
from common_layer.xml.txc.models import TXCService
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape, to_shape  # type: ignore
from shapely import LineString, MultiLineString
from shapely.ops import linemerge, transform
from structlog.stdlib import get_logger

from ..api.geometry import OSRMGeometryAPI
from ..helpers import TrackLookup

log = get_logger()

SRID = 4326


def has_sufficient_track_data(
    tracks: TrackLookup,
    stop_sequence: list[NaptanStopPoint],
) -> bool:
    """
    Check that there is sufficient track data for storing distance info

    Validates that:
    - A track exists between every stop in sequence
    - Each track has a geometry with at least 3 points
    """
    expected_track_count = len(stop_sequence) - 1
    for i in range(expected_track_count):
        from_stop = stop_sequence[i]
        to_stop = stop_sequence[i + 1]
        track = tracks.get((from_stop.atco_code, to_stop.atco_code))

        if not track:
            log.warning(
                "No track data for stop point pair",
                from_atco_code=from_stop.atco_code,
                to_atco_code=to_stop.atco_code,
            )
            return False

        if not track.geometry:
            log.warning(
                "Track has no geometry",
                track_id=track.id,
            )
            return False

        shapely_geom = to_shape(track.geometry)
        coords = list(shapely_geom.coords)
        if len(coords) < 3:
            log.debug(f"Track has insufficient points: {len(coords)}")
            return False

    return True


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great-circle distance in meters between two points (lon/lat).
    """
    earth_radius = 6371000  # Earth radius in meters
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return earth_radius * c


def snap_linestrings(
    lines: list[LineString], tolerance: float | None = 15.0
) -> list[LineString]:
    """
    Snap the end of each linestring to the start of the next.
    If tolerance is None, always snap regardless of distance.
    Otherwise, snap only when distance <= tolerance (meters).
    """
    if not lines:
        return []

    snapped: list[LineString] = [LineString(lines[0].coords)]
    for _idx, curr in enumerate(lines[1:], start=1):
        prev: LineString = snapped[-1]
        prev_end = prev.coords[-1]
        curr_start = curr.coords[0]

        curr_coords = list(curr.coords)

        if tolerance is None:
            # Always snap, skip distance check
            curr_coords[0] = tuple(prev_end)
        else:
            dist: float = haversine(
                prev_end[0],
                prev_end[1],
                curr_start[0],
                curr_start[1],
            )
            if dist <= tolerance:
                curr_coords[0] = tuple(prev_end)

        snapped.append(LineString(curr_coords))

    return snapped


def get_geometry_and_distance_from_tracks(
    tracks: TrackLookup,
    stop_sequence: list[NaptanStopPoint],
) -> tuple[WKBElement | None, int, int]:
    """
    Calculate the full service geometry and distance using track data,
    snapping endpoints together within 15 meters.
    """
    total_distance = 0
    txc_total_distance = 0
    track_linestrings: list[LineString] = []
    snapped_lines: list[LineString] = []

    # Define a projection transformer if your data is in lat/lon (WGS84)
    project = pyproj.Transformer.from_crs(
        "EPSG:4326", "EPSG:27700", always_xy=True
    ).transform

    for i, (from_stop, to_stop) in enumerate(zip(stop_sequence, stop_sequence[1:])):
        track = tracks.get((from_stop.atco_code, to_stop.atco_code))
        if not track or not track.geometry:
            raise ValueError(
                f"No track or geometry found for stop point \
                pair {from_stop.atco_code} -> {to_stop.atco_code} at index {i}"
            )
        if track.distance:
            txc_total_distance += track.distance

        shapely_geom = to_shape(track.geometry)
        segment_length = 0.0
        geom_metric = transform(project, shapely_geom)
        if isinstance(shapely_geom, LineString):
            track_linestrings.append(shapely_geom)
            segment_length = float(geom_metric.length)
        elif isinstance(shapely_geom, MultiLineString):
            track_linestrings.extend(shapely_geom.geoms)
            segment_length = sum(
                float(line.length)
                for line in geom_metric.geoms
                if isinstance(line, LineString)
            )
        else:
            log.warning(
                "Track has unexpected geometry type",
                track_id=track.id,
                geom_type=shapely_geom.geom_type,
            )
        total_distance += segment_length

        if not track_linestrings:
            log.warning("No valid track geometries found for stop sequence.")
            return None, 0, 0

    # Snap endpoints before merging
    snapped_lines = snap_linestrings(track_linestrings, tolerance=None)
    merged = linemerge(snapped_lines)
    if isinstance(merged, MultiLineString):
        # Flatten all coordinates into a single LineString
        coords: list[tuple[float, float]] = []
        for line in merged.geoms:
            coords.extend(list(line.coords))  # type: ignore
        merged = LineString(coords)

    geometry = from_shape(merged, srid=SRID)
    return geometry, int(total_distance), txc_total_distance


def process_service_pattern_distance(
    service: TXCService,
    service_pattern_id: int,
    tracks: TrackLookup,
    stop_sequence: list[NaptanStopPoint],
    db: SqlDB,
) -> int | None:
    """
    Calculate and store the total distance of this service pattern
    Uses tracks data if available in the file, else uses distance service
    """
    if service.FlexibleService:
        return None

    distance: int | None = None
    txc_distance: int | None = None
    geometry: WKBElement | None = None
    if tracks and has_sufficient_track_data(tracks, stop_sequence):
        geometry, distance, txc_distance = get_geometry_and_distance_from_tracks(
            tracks, stop_sequence
        )
    else:
        api = OSRMGeometryAPI()
        coords = [(stop.shape.x, stop.shape.y) for stop in stop_sequence]
        geometry, distance = api.get_geometry_and_distance(coords)

    repo = TransmodelServicePatternDistanceRepo(db)
    service_pattern_distance = TransmodelServicePatternDistance(
        service_pattern_id=service_pattern_id,
        distance=distance,
        txc_distance=txc_distance,
        geom=geometry,
    )
    repo.insert(service_pattern_distance)

    return distance
