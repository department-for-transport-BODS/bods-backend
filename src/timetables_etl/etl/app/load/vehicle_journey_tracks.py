"""
Process and add Vehicle Journey Tracks to DB
"""

from structlog.stdlib import get_logger

from ..database.client import BodsDB
from ..database.models import TransmodelTracksVehicleJourney
from ..database.models.model_transmodel_vehicle_journey import TransmodelVehicleJourney
from ..database.repos import TransmodelTracksVehicleJourneyRepo
from ..helpers import TrackLookup
from ..transform.vehicle_journey_tracks import generate_vehicle_journey_tracks
from ..txc.models import TXCData, TXCFlexibleJourneyPattern, TXCJourneyPattern

log = get_logger()


def load_vehicle_journey_tracks(
    journey_pattern: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    vehicle_journeys: list[TransmodelVehicleJourney],
    track_lookup: TrackLookup,
    txc: TXCData,
    db: BodsDB,
) -> list[TransmodelTracksVehicleJourney]:
    """
    Generate Vehicle Journey Tracks
    """
    vj_tracks = generate_vehicle_journey_tracks(
        journey_pattern, vehicle_journeys, track_lookup, txc
    )

    result = TransmodelTracksVehicleJourneyRepo(db).bulk_insert(vj_tracks)

    log.info("Added VJ to Track Links to Database", count=len(result))
    return result
