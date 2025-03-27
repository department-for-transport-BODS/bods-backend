"""
transmodel_service_patternstops
"""

from typing import Sequence

from common_layer.database.client import SqlDB
from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
)
from common_layer.database.models.model_transmodel_vehicle_journey import (
    TransmodelVehicleJourney,
)
from common_layer.database.repos import TransmodelServicePatternStopRepo
from common_layer.xml.txc.models import (
    TXCFlexibleJourneyPattern,
    TXCFlexibleVehicleJourney,
    TXCVehicleJourney,
)
from structlog.stdlib import get_logger

from ..transform.models_context import GeneratePatternStopsContext
from ..transform.service_pattern_stops import generate_pattern_stops
from ..transform.service_pattern_stops_flexible import generate_flexible_pattern_stops
from .models_context import ProcessPatternStopsContext

log = get_logger()


def process_pattern_stops(
    tm_service_pattern: TransmodelServicePattern,
    tm_vehicle_journey: TransmodelVehicleJourney,
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
    context: ProcessPatternStopsContext,
) -> list[TransmodelServicePatternStop]:
    """
    Process and insert transmodel_servicepatternstop
    """
    pattern_stops = generate_pattern_stops(
        tm_service_pattern,
        tm_vehicle_journey,
        txc_vehicle_journey,
        GeneratePatternStopsContext(
            context.jp_sections,
            context.stop_sequence,
            context.stop_activity_id_map,
            context.naptan_stops_lookup,
        ),
    )

    results = TransmodelServicePatternStopRepo(context.db).bulk_insert(pattern_stops)

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
    stop_activity_id_map: dict[str, int],
    db: SqlDB,
) -> list[TransmodelServicePatternStop]:
    """Process stops for flexible patterns"""

    pattern_stops = generate_flexible_pattern_stops(
        tm_service_pattern,
        tm_vehicle_journey,
        flexible_pattern,
        stop_sequence,
        stop_activity_id_map,
    )

    results = TransmodelServicePatternStopRepo(db).bulk_insert(pattern_stops)

    log.info(
        "Saved Flexible Service Pattern Stops for Vehicle Journey",
        pattern_id=tm_service_pattern.id,
        vehicle_journey_id=tm_vehicle_journey.id,
        stop_count=len(results),
    )

    return results
