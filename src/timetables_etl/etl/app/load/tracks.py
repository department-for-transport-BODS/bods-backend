"""
Tracks Generation
"""

from common_layer.database import SqlDB
from common_layer.xml.txc.models import TXCRouteSection
from structlog.stdlib import get_logger

from ..helpers import TrackLookup
from ..transform.tracks import create_new_tracks

log = get_logger()


def build_track_lookup(
    route_sections: list[TXCRouteSection], db: SqlDB, skip_inserts: bool = False
) -> TrackLookup:
    """
    Process tracks from route sections
    Returns a lookup dictionary mapping (from_atco, to_atco) to TransmodelTracks
    """
    log_ctx = log.bind()
    all_tracks = create_new_tracks(route_sections)
    log_ctx.info(
        "Built track lookup from route sections", tracks_in_txc=len(all_tracks)
    )
    return {(track.from_atco_code, track.to_atco_code): track for track in all_tracks}
