"""
Process and add Vehicle Journey Tracks to DB
"""

from common_layer.database.client import SqlDB
from common_layer.database.models import NaptanStopPoint, TransmodelServicePatternTracks
from common_layer.database.repos import (
    TransmodelServicePatternTracksRepo,
    TransmodelTrackRepo,
)
from common_layer.xml.txc.helpers.routes import extract_stop_point_pairs
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
    skip_inserts: bool = False,
) -> list[TransmodelServicePatternTracks]:
    """
    Load tracks data:
    - Selects tracks from the lookup for this service pattern
    - Inserts them if they haven't already been inserted
    """

    # Extract the needed (from, to) pairs for this service pattern
    stop_point_pairs = extract_stop_point_pairs(stop_sequence)
    tracks_in_service_pattern = [
        track
        for track in track_lookup.values()
        if (track.from_atco_code, track.to_atco_code) in stop_point_pairs
    ]
    if not skip_inserts:
        # Create tracks for this service pattern if they haven't
        # been inserted already
        uninserted_tracks = [
            track for track in tracks_in_service_pattern if not getattr(track, "id")
        ]
        track_repo = TransmodelTrackRepo(db)
        track_ids = track_repo.bulk_insert_ignore_duplicates(uninserted_tracks)

        # Set ID on inserted tracks in lookup
        for (from_code, to_code), track_id in track_ids.items():
            track = track_lookup.get((from_code, to_code))
            if track:
                track.id = track_id
            else:
                log.error(
                    "Track not found in lookup", from_code=from_code, to_code=to_code
                )
                raise ValueError("Track not found")

        log.info(
            "Added new tracks to database",
            new_tracks_count=len(track_ids),
        )
    else:
        log.info("Skipped inserting tracks")

    sp_tracks = generate_service_pattern_tracks(
        journey_pattern, service_pattern_id, track_lookup, stop_point_pairs
    )

    if not skip_inserts:
        TransmodelServicePatternTracksRepo(db).bulk_insert(sp_tracks)
        log.info("Inserted SP -> Track links", count=len(sp_tracks))
    else:
        log.info("Skipped inserting SP -> Track links")

    return sp_tracks
