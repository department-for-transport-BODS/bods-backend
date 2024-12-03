"""
Tracks Generation
"""

from structlog.stdlib import get_logger

from ..database import BodsDB
from ..database.repos import TransmodelTrackRepo
from ..helpers import TrackLookup
from ..transform.tracks import analyze_track_pairs, create_new_tracks
from ..txc.helpers.routes import extract_stop_point_pairs
from ..txc.models import TXCRouteSection

log = get_logger()


def load_tracks(route_sections: list[TXCRouteSection], db: BodsDB) -> TrackLookup:
    """
    Process tracks from route sections, creating new ones if they don't exist.
    Returns a lookup dictionary mapping (from_atco, to_atco) to TransmodelTracks
    """
    log_ctx = log.bind()
    track_repo = TransmodelTrackRepo(db)
    route_pairs = extract_stop_point_pairs(route_sections)

    existing_tracks = track_repo.get_by_stop_pairs(route_pairs)
    analysis = analyze_track_pairs(route_pairs, existing_tracks)

    all_tracks = existing_tracks
    if analysis.pairs_to_create:
        new_tracks = create_new_tracks(analysis.pairs_to_create, route_sections)
        track_repo.bulk_insert(new_tracks)
        all_tracks = existing_tracks + new_tracks

        log_ctx.info(
            "Fetched Existing and Added new tracks to database",
            new_tracks_count=len(new_tracks),
            existing_tracks=len(existing_tracks),
            total_tracks=len(all_tracks),
        )

    return {(track.from_atco_code, track.to_atco_code): track for track in all_tracks}
