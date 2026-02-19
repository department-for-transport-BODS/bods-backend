# pyright: reportUnusedImport=false
"""
Functions for loading Service Pattern Distance
"""

from math import asin, cos, radians, sin, sqrt

from common_layer.database import SqlDB
from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicePatternDistance,
    TransmodelTracks,
)
from common_layer.database.repos import TransmodelServicePatternDistanceRepo
from common_layer.xml.txc.models import TXCService
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape, to_shape  # type: ignore
from shapely import LineString, MultiLineString
from shapely.ops import linemerge
from structlog.stdlib import get_logger

from ..api.geometry import OSRMGeometryAPI
from ..helpers import TrackLookup

log = get_logger()

SRID = 4326


AnalyzedSegment = tuple[NaptanStopPoint, NaptanStopPoint, TransmodelTracks | None]


def _count_geometry_coords(geom: LineString | MultiLineString) -> int:
    """Count total coordinate points in a geometry (handles both LineString and MultiLineString)."""
    if isinstance(geom, MultiLineString):
        return sum(len(line.coords) for line in geom.geoms)
    return len(geom.coords)


def analyze_track_segments(
    tracks: TrackLookup,
    stop_sequence: list[NaptanStopPoint],
) -> list[AnalyzedSegment]:
    """
    Analyze track data for each stop pair in route order.

    Returns an ordered list of segments. Each segment includes the track
    if it exists and has geometry with 3+ points, otherwise None.
    """
    segments: list[AnalyzedSegment] = []

    for from_stop, to_stop in zip(stop_sequence, stop_sequence[1:]):
        track = tracks.get((from_stop.atco_code, to_stop.atco_code))

        if track and track.geometry:
            shapely_geom = to_shape(track.geometry)
            if (
                isinstance(shapely_geom, (LineString, MultiLineString))
                and _count_geometry_coords(shapely_geom) >= 3
            ):
                segments.append((from_stop, to_stop, track))
            else:
                segments.append((from_stop, to_stop, None))
        else:
            segments.append((from_stop, to_stop, None))

    return segments


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


def _to_linestring(
    shapely_geom: LineString | MultiLineString,
) -> LineString:
    """Convert geometry to a single LineString, merging if needed."""
    if isinstance(shapely_geom, MultiLineString):
        all_coords: list[tuple[float, float]] = []
        for line in shapely_geom.geoms:
            all_coords.extend(list(line.coords))  # type: ignore
        return LineString(all_coords)
    return shapely_geom


def _process_track_segment(
    track: TransmodelTracks,
    linestrings: list[LineString],
) -> tuple[int, int]:
    """Process a segment with track data. Returns (distance, coord_distance)."""
    if track.geometry is not None:
        shapely_geom = to_shape(track.geometry)
        if isinstance(shapely_geom, (LineString, MultiLineString)):
            linestrings.append(_to_linestring(shapely_geom))
        else:
            raise TypeError(
                "Expected LineString or MultiLineString from track geometry"
            )
    return track.distance or 0, track.coord_distance or 0


def _process_osrm_segment(
    from_stop: NaptanStopPoint,
    to_stop: NaptanStopPoint,
    api: OSRMGeometryAPI,
    linestrings: list[LineString],
) -> int:
    """Process a segment without track data using OSRM. Returns distance."""
    coords = [
        (from_stop.shape.x, from_stop.shape.y),
        (to_stop.shape.x, to_stop.shape.y),
    ]
    seg_geometry, seg_distance = api.get_geometry_and_distance(coords)
    if seg_geometry:
        shapely_geom = to_shape(seg_geometry)
        if isinstance(shapely_geom, (LineString, MultiLineString)):
            linestrings.append(_to_linestring(shapely_geom))
        else:
            raise TypeError("Expected LineString or MultiLineString from OSRM geometry")
    return seg_distance or 0


def _merge_linestrings(linestrings: list[LineString]) -> LineString:
    """Merge and snap linestrings into a single LineString."""
    snapped = snap_linestrings(linestrings, tolerance=None)
    merged = linemerge(snapped)
    if isinstance(merged, MultiLineString):
        all_coords: list[tuple[float, float]] = []
        for line in merged.geoms:
            all_coords.extend(list(line.coords))  # type: ignore
        merged = LineString(all_coords)
    return merged


def get_geometry_and_distance_from_tracks(
    segments: list[AnalyzedSegment],
) -> tuple[WKBElement | None, int, int]:
    """
    Calculate the full service geometry and distance in route order.
    Uses track data for good segments, OSRM for bad segments.
    Returns (geometry, coord_track_distance, distance).
    """
    total_distance = 0
    total_coord_distance = 0
    linestrings: list[LineString] = []
    api: OSRMGeometryAPI | None = None

    for from_stop, to_stop, track in segments:
        if track:
            distance, coord_distance = _process_track_segment(track, linestrings)
            total_distance += distance
            total_coord_distance += coord_distance
        else:
            if api is None:
                api = OSRMGeometryAPI()
            total_distance += _process_osrm_segment(
                from_stop, to_stop, api, linestrings
            )

    if not linestrings:
        return None, 0, 0

    merged = _merge_linestrings(linestrings)
    geometry = from_shape(merged, srid=SRID)
    return geometry, total_coord_distance, total_distance


def process_service_pattern_distance(
    service: TXCService,
    service_pattern_id: int,
    tracks: TrackLookup,
    stop_sequence: list[NaptanStopPoint],
    db: SqlDB,
) -> int | None:
    """
    Calculate and store the total distance of this service pattern.
    Uses track data where sufficient, falls back to OSRM per-segment otherwise.
    """
    if service.FlexibleService:
        return None

    distance: int | None = None
    coord_track_distance: int | None = None
    geometry: WKBElement | None = None

    if tracks:
        segments = analyze_track_segments(tracks, stop_sequence)
        geometry, coord_track_distance, distance = (
            get_geometry_and_distance_from_tracks(segments)
        )
    else:
        api = OSRMGeometryAPI()
        coords = [(stop.shape.x, stop.shape.y) for stop in stop_sequence]
        geometry, distance = api.get_geometry_and_distance(coords)

    repo = TransmodelServicePatternDistanceRepo(db)
    service_pattern_distance = TransmodelServicePatternDistance(
        service_pattern_id=service_pattern_id,
        distance=distance,
        coord_track_distance=coord_track_distance,
        geom=geometry,
    )
    repo.insert(service_pattern_distance)

    return distance
