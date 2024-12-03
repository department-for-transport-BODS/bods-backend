"""
Transmodel Tracks Generation
"""

from dataclasses import dataclass
from typing import NamedTuple

import pyproj
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely import LineString, Point
from structlog.stdlib import get_logger

from ..database.models.model_transmodel import TransmodelTracks
from ..txc.models import TXCTrack
from ..txc.models.txc_route import TXCRouteSection

log = get_logger()


@dataclass
class TrackPairAnalysis:
    """Result of analyzing which track pairs exist and which need to be created"""

    existing_tracks: list[TransmodelTracks]
    pairs_to_create: list[tuple[str, str]]


def analyze_track_pairs(
    route_pairs: list[tuple[str, str]], existing_tracks: list[TransmodelTracks]
) -> TrackPairAnalysis:
    """
    Analyze which track pairs already exist and which need to be created.
    """
    log_ctx = log.bind(total_pairs=len(route_pairs))

    unique_pairs = list(dict.fromkeys(route_pairs))
    log_ctx.debug(
        "Processing unique track pairs",
        total_unique=len(unique_pairs),
        duplicate_pairs=len(route_pairs) - len(unique_pairs),
    )

    existing_pairs = {
        (track.from_atco_code, track.to_atco_code) for track in existing_tracks
    }
    pairs_to_create = [pair for pair in unique_pairs if pair not in existing_pairs]

    log_ctx.info(
        "Track pair analysis complete",
        existing_tracks=len(existing_pairs),
        new_tracks_needed=len(pairs_to_create),
    )

    return TrackPairAnalysis(
        existing_tracks=existing_tracks, pairs_to_create=pairs_to_create
    )


class TrackGeometry(NamedTuple):
    """Contains processed geometry and distance for a track"""

    geometry: WKBElement
    line: LineString
    distance: int | None


def calculate_distance_from_geometry(line: LineString) -> int | None:
    """
    Calculate PyProj geodesic distance in meters from a LineString geometry.
    Gets list of coodinates of line string and then adding the distances between points
    """
    geod = pyproj.Geod(ellps="WGS84")

    try:
        coords = list(line.coords)
        total_distance = 0

        for i in range(len(coords) - 1):
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[i + 1]

            _, _, distance = geod.inv(lons1=lon1, lats1=lat1, lons2=lon2, lats2=lat2)
            total_distance += distance

        return int(total_distance)

    except Exception as e:
        log.warning("Failed to calculate geodesic distance", error=str(e))
        return None


def process_track_geometry(track: TXCTrack) -> TrackGeometry | None:
    """
    Process a TXC track to extract geometry.
    Returns None if track has no valid mapping data.
    """
    if not track or not track.Mapping or not track.Mapping.Location:
        return None

    # Need at least 2 points to make a line
    if len(track.Mapping.Location) < 2:
        return None

    try:
        points = [
            Point(float(loc.Longitude), float(loc.Latitude))
            for loc in track.Mapping.Location
        ]

        line = LineString(points)

        geometry = from_shape(line, srid=4326)

        return TrackGeometry(geometry=geometry, line=line, distance=None)

    except (ValueError, TypeError) as e:
        log.warning(
            "Failed to process track geometry",
            error=str(e),
            track_points=len(track.Mapping.Location) if track.Mapping else 0,
        )
        return None


def create_new_tracks(
    pairs: list[tuple[str, str]], route_sections: list[TXCRouteSection]
) -> list[TransmodelTracks]:
    """
    Create new TransmodelTrack objects with geometry and distance where available.
    """
    track_mapping: dict[tuple[str, str], tuple[TXCTrack, int | None]] = {}
    for section in route_sections:
        for route_link in section.RouteLink:
            if route_link.Track:
                track_mapping[(route_link.From, route_link.To)] = (
                    route_link.Track,
                    route_link.Distance,
                )

    new_tracks: list[TransmodelTracks] = []
    for from_code, to_code in pairs:
        mapping = track_mapping.get((from_code, to_code))

        if mapping:
            txc_track, provided_distance = mapping
            track_geom = process_track_geometry(txc_track)

            if track_geom:
                # Calculate distance from LineString if not provided
                distance = (
                    provided_distance
                    if provided_distance is not None
                    else calculate_distance_from_geometry(track_geom.line)
                )

                new_tracks.append(
                    TransmodelTracks(
                        from_atco_code=from_code,
                        to_atco_code=to_code,
                        geometry=track_geom.geometry,
                        distance=distance,
                    )
                )

    log.info(
        "Created new tracks",
        total_tracks=len(new_tracks),
        with_geometry=sum(1 for t in new_tracks if t.geometry is not None),
        with_distance=sum(1 for t in new_tracks if t.distance is not None),
    )

    return new_tracks
