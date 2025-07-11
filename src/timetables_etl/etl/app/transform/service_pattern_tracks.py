"""
Vehicle Journey Tracks Generation
"""

from common_layer.database.models import TransmodelServicePatternTracks
from common_layer.xml.txc.models import TXCFlexibleJourneyPattern, TXCJourneyPattern
from structlog.stdlib import get_logger

from ..helpers import TrackLookup

log = get_logger()


def generate_standard_service_tracks(
    journey_pattern: TXCJourneyPattern,
    service_pattern_id: int,
    stop_point_pairs: list[tuple[str, str]],
    track_lookup: TrackLookup,
) -> list[TransmodelServicePatternTracks]:
    """
    Generate the tracks for a StandardService
    """
    log_ctx = log.bind(
        journey_pattern_id=journey_pattern.id,
    )
    sp_tracks: list[TransmodelServicePatternTracks] = []

    for sequence_number, (from_code, to_code) in enumerate(stop_point_pairs):
        track = track_lookup.get((from_code, to_code))
        if track and track.id:
            sp_tracks.append(
                TransmodelServicePatternTracks(
                    sequence_number=sequence_number,
                    tracks_id=track.id,
                    service_pattern_id=service_pattern_id,
                )
            )

    log_ctx.info(
        "Generated service pattern tracks",
        tracks_created=len(sp_tracks),
        stop_sequence_count=len(stop_point_pairs),
    )

    return sp_tracks


def generate_flexible_service_tracks(_journey_pattern: TXCFlexibleJourneyPattern):
    """
    Generate the tracks for a StandardService
    """
    log.error("Flexible Service Tracks Not Implemented!")


def generate_service_pattern_tracks(
    journey_pattern: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    service_pattern_id: int,
    track_lookup: TrackLookup,
    stop_point_pairs: list[tuple[str, str]],
) -> list[TransmodelServicePatternTracks]:
    """
    Create Vehicle Journey Tracks
    """
    match journey_pattern:
        case TXCJourneyPattern():
            return generate_standard_service_tracks(
                journey_pattern=journey_pattern,
                service_pattern_id=service_pattern_id,
                stop_point_pairs=stop_point_pairs,
                track_lookup=track_lookup,
            )
        case TXCFlexibleJourneyPattern():
            generate_flexible_service_tracks(journey_pattern)
            return []
        case _:
            raise ValueError(f"Unknown Journey Pattern type: {type(journey_pattern)}")
