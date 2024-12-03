"""
transmodel_service_patternstops
"""

from typing import Sequence

from structlog.stdlib import get_logger

from ..database.client import BodsDB
from ..database.models import (
    NaptanStopPoint,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelVehicleJourney,
)
from ..database.repos import (
    TransmodelServicePatternStopRepo,
    TransmodelStopActivityRepo,
)
from ..transform.service_pattern_stops import generate_pattern_stops
from ..transform.service_pattern_stops_flexible import generate_flexible_pattern_stops
from ..txc.models import (
    TXCFlexibleJourneyPattern,
    TXCFlexibleVehicleJourney,
    TXCJourneyPatternSection,
    TXCVehicleJourney,
)

log = get_logger()


def process_pattern_stops(
    tm_service_pattern: TransmodelServicePattern,
    tm_vehicle_journey: TransmodelVehicleJourney,
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
    jp_sections: list[TXCJourneyPatternSection],
    stop_sequence: Sequence[NaptanStopPoint],
    db: BodsDB,
) -> list[TransmodelServicePatternStop]:
    """
    Process and insert transmodel_servicepatternstop
    """
    activity_map = TransmodelStopActivityRepo(db).get_activity_map()

    pattern_stops = generate_pattern_stops(
        tm_service_pattern,
        tm_vehicle_journey,
        txc_vehicle_journey,
        jp_sections,
        stop_sequence,
        activity_map,
    )

    results = TransmodelServicePatternStopRepo(db).bulk_insert(pattern_stops)

    log.info(
        "Saved Service Pattern Stops for Vehicle Journey",
        pattern_id=tm_service_pattern.id,
        vehicle_journey_id=tm_vehicle_journey.id,
        stop_count=len(results),
    )

    return results


def process_flexible_pattern_stops(
    tm_service_pattern: TransmodelServicePattern,
    tm_vehicle_journey: TransmodelVehicleJourney,
    flexible_pattern: TXCFlexibleJourneyPattern,
    stop_sequence: Sequence[NaptanStopPoint],
    db: BodsDB,
) -> list[TransmodelServicePatternStop]:
    """Process stops for flexible patterns"""
    activity_map = TransmodelStopActivityRepo(db).get_activity_map()

    pattern_stops = generate_flexible_pattern_stops(
        tm_service_pattern,
        tm_vehicle_journey,
        flexible_pattern,
        stop_sequence,
        activity_map,
    )

    results = TransmodelServicePatternStopRepo(db).bulk_insert(pattern_stops)

    log.info(
        "Saved Flexible Service Pattern Stops for Vehicle Journey",
        pattern_id=tm_service_pattern.id,
        vehicle_journey_id=tm_vehicle_journey.id,
        stop_count=len(results),
    )

    return results
