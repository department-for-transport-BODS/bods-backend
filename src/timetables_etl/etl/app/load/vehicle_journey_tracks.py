"""
Process and add Vehicle Journey Tracks to DB
"""

from common_layer.database.client import SqlDB
from common_layer.database.models import TransmodelTracksVehicleJourney
from common_layer.database.models.model_transmodel_vehicle_journey import (
    TransmodelVehicleJourney,
)
from common_layer.database.repos import TransmodelTracksVehicleJourneyRepo
from common_layer.xml.txc.models import (
    TXCData,
    TXCFlexibleJourneyPattern,
    TXCJourneyPattern,
)
from structlog.stdlib import get_logger

from ..helpers import TrackLookup
from ..transform.vehicle_journey_tracks import generate_vehicle_journey_tracks

log = get_logger()


def load_vehicle_journey_tracks(
    journey_pattern: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    vehicle_journeys: list[TransmodelVehicleJourney],
    track_lookup: TrackLookup,
    txc: TXCData,
    db: SqlDB,
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
