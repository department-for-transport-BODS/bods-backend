"""
Functions for loading Service Pattern Distance
"""

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
from shapely.ops import linemerge
from structlog.stdlib import get_logger

from ..api.geometry import OSRMGeometryAPI
from ..helpers import TrackLookup

log = get_logger()


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


def get_geometry_and_distance_from_tracks(
    tracks: TrackLookup,
    stop_sequence: list[NaptanStopPoint],
) -> tuple[WKBElement | None, int]:
    """
    Calculate the full service geometry and distance using track data
    """

    total_distance: int = 0
    geometry: WKBElement | None = None

    track_linestrings: list[LineString] = []
    for i in range(len(stop_sequence) - 1):
        from_stop = stop_sequence[i]
        to_stop = stop_sequence[i + 1]

        track = tracks.get((from_stop.atco_code, to_stop.atco_code))
        if not track:
            raise ValueError(
                "No track found for stop point pair",
            )
        if not track.geometry:
            raise ValueError("Missing geometry for track")

        if track.distance:
            total_distance += track.distance

        shapely_geom = to_shape(track.geometry)

        if isinstance(shapely_geom, LineString):
            track_linestrings.append(shapely_geom)
        elif isinstance(shapely_geom, MultiLineString):
            track_linestrings.extend(shapely_geom.geoms)
        else:
            log.warning(
                "Track has unexpected geometry type",
                track_id=track.id,
                geom_type=shapely_geom.geom_type,
            )

    if track_linestrings:
        merged = linemerge(track_linestrings)

        if isinstance(merged, MultiLineString):
            # Flatten all coordinates into a single LineString
            coords: list[tuple[float, float]] = []
            for line in merged.geoms:
                coords.extend(list(line.coords))  # type: ignore
            merged = LineString(coords)

        geometry = from_shape(merged, srid=4326)

    return geometry, total_distance


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
    geometry: WKBElement | None = None
    if tracks and has_sufficient_track_data(tracks, stop_sequence):
        geometry, distance = get_geometry_and_distance_from_tracks(
            tracks, stop_sequence
        )
    else:
        return None
        # TODO: Re-enable once OSRM API deployed
        # api = OSRMGeometryAPI()
        # coords = [(stop.shape.x, stop.shape.y) for stop in stop_sequence]
        # geometry, distance = api.get_geometry_and_distance(coords)

    repo = TransmodelServicePatternDistanceRepo(db)
    service_pattern_distance = TransmodelServicePatternDistance(
        service_pattern_id=service_pattern_id, distance=distance, geom=geometry
    )
    repo.insert(service_pattern_distance)

    return distance
