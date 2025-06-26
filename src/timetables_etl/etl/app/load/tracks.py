"""
Tracks Generation
"""

from common_layer.database import SqlDB
from common_layer.database.repos import TransmodelTrackRepo
from common_layer.xml.txc.models import TXCRouteSection
from structlog.stdlib import get_logger

from ..helpers import TrackLookup
from ..transform.tracks import create_new_tracks

log = get_logger()


def load_tracks(
    route_sections: list[TXCRouteSection], db: SqlDB, skip_inserts: bool = False
) -> TrackLookup:
    """
    Process tracks from route sections, creating new ones if they don't exist.
    Returns a lookup dictionary mapping (from_atco, to_atco) to TransmodelTracks
    """
    log_ctx = log.bind()
    new_tracks = create_new_tracks(route_sections)

    track_ids = {}
    if not skip_inserts:
        track_repo = TransmodelTrackRepo(db)
        track_ids = track_repo.bulk_insert_ignore_duplicates(new_tracks)
        log_ctx.info(
            "Added new tracks to database",
            new_tracks_count=len(new_tracks),
        )
    else:
        log_ctx.info("Skipped inserting tracks")

    return {
        (track.from_atco_code, track.to_atco_code): (
            setattr(
                track,
                "id",
                track_ids.get((track.from_atco_code, track.to_atco_code), None),
            )
            or track
        )
        for track in new_tracks
    }
