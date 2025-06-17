"""
Process and add Vehicle Journey Tracks to DB
"""

from common_layer.database.client import SqlDB
from common_layer.database.models import NaptanStopPoint, TransmodelServicePatternTracks
from common_layer.database.repos import TransmodelServicePatternTracksRepo
from common_layer.xml.txc.models import TXCFlexibleJourneyPattern, TXCJourneyPattern
from structlog.stdlib import get_logger

from ..helpers import TrackLookup
from ..transform.service_pattern_tracks import generate_service_pattern_tracks

log = get_logger()


def load_service_pattern_tracks(
    journey_pattern: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    service_pattern_id: int,
    track_lookup: TrackLookup,
    stop_sequence: list[NaptanStopPoint],
    db: SqlDB,
) -> list[TransmodelServicePatternTracks]:
    """
    Generate Vehicle Journey Tracks
    """
    sp_tracks = generate_service_pattern_tracks(
        journey_pattern, service_pattern_id, track_lookup, stop_sequence
    )

    result = TransmodelServicePatternTracksRepo(db).bulk_insert(sp_tracks)

    log.info("Added SP to Track Links to Database", count=len(result))
    return result
