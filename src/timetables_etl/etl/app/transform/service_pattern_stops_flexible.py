"""
Flexible Service Pattern Stop Handling
"""

from typing import Sequence

from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelStopActivity,
)
from common_layer.database.models.model_transmodel_vehicle_journey import (
    TransmodelVehicleJourney,
)
from common_layer.txc.helpers.service import get_stop_activity_details
from common_layer.txc.models import TXCFlexibleJourneyPattern
from common_layer.txc.models.txc_service_flexible import (
    TXCFixedStopUsage,
    TXCFlexibleStopUsage,
)
from structlog.stdlib import get_logger

log = get_logger()


def find_naptan_stop(
    stop_ref: str,
    stop_sequence: Sequence[NaptanStopPoint],
) -> NaptanStopPoint | None:
    """
    Find a NaptanStopPoint in the sequence by reference

    """
    naptan_stop = next((s for s in stop_sequence if s.atco_code == stop_ref), None)
    if not naptan_stop:
        log.warning(
            "Stop not found in sequence", stop_ref=stop_ref, stop_sequence=stop_sequence
        )
    return naptan_stop


def create_flexible_stop(
    stop_ref: str,
    naptan_stop: NaptanStopPoint,
    service_pattern: TransmodelServicePattern,
    vehicle_journey: TransmodelVehicleJourney,
    sequence_number: int,
    is_timing_point: bool,
    activity_id: int,
) -> TransmodelServicePatternStop:
    """
    Create a service pattern stop for flexible services
    Flexible Services don't have departure times
    """
    return TransmodelServicePatternStop(
        sequence_number=sequence_number,
        atco_code=stop_ref,
        naptan_stop_id=naptan_stop.id if naptan_stop else None,
        service_pattern_id=service_pattern.id,
        departure_time=None,
        is_timing_point=is_timing_point,
        txc_common_name=naptan_stop.common_name if naptan_stop else None,
        vehicle_journey_id=vehicle_journey.id,
        stop_activity_id=activity_id,
        auto_sequence_number=sequence_number,
    )


def process_sequence_stop(
    stop_point: TXCFixedStopUsage | TXCFlexibleStopUsage,
    stop_sequence: Sequence[NaptanStopPoint],
    service_pattern: TransmodelServicePattern,
    vehicle_journey: TransmodelVehicleJourney,
    sequence_number: int,
    activity_map: dict[str, TransmodelStopActivity],
) -> TransmodelServicePatternStop | None:
    """
    Process a single stop in the sequence

    """
    naptan_stop = find_naptan_stop(stop_point.StopPointRef, stop_sequence)
    if not naptan_stop:
        return None

    try:
        is_timing_point, activity_type = get_stop_activity_details(stop_point)
    except ValueError as e:
        log.warning(
            "Unknown stop type", error=str(e), vehicle_journey_id=vehicle_journey.id
        )
        return None

    activity = activity_map.get(activity_type)
    if not activity:
        log.error(
            "Stop activity not found - skipping stop",
            requested_activity=activity_type,
            available_activities=list(activity_map.keys()),
            stop_point=stop_point.StopPointRef,
            vehicle_journey_id=vehicle_journey.id,
        )
        return None

    return create_flexible_stop(
        stop_ref=stop_point.StopPointRef,
        naptan_stop=naptan_stop,
        service_pattern=service_pattern,
        vehicle_journey=vehicle_journey,
        sequence_number=sequence_number,
        is_timing_point=is_timing_point,
        activity_id=activity.id,
    )


def generate_flexible_pattern_stops(
    service_pattern: TransmodelServicePattern,
    vehicle_journey: TransmodelVehicleJourney,
    flexible_pattern: TXCFlexibleJourneyPattern,
    stop_sequence: Sequence[NaptanStopPoint],
    activity_map: dict[str, TransmodelStopActivity],
) -> list[TransmodelServicePatternStop]:
    """Generate service pattern stops for a flexible service"""
    log.info(
        "Starting flexible pattern stops generation",
        stop_count=len(stop_sequence),
        activity_count=len(activity_map),
        pattern_id=flexible_pattern.id,
    )

    pattern_stops: list[TransmodelServicePatternStop] = []
    auto_sequence: int = 0

    # Process main sequence stops
    for stop_point in flexible_pattern.StopPointsInSequence:
        if stop := process_sequence_stop(
            stop_point,
            stop_sequence,
            service_pattern,
            vehicle_journey,
            auto_sequence,
            activity_map,
        ):
            pattern_stops.append(stop)
            auto_sequence += 1

    # Process flexible zones
    for zone in flexible_pattern.FlexibleZones:
        if stop := process_sequence_stop(
            zone,
            stop_sequence,
            service_pattern,
            vehicle_journey,
            auto_sequence,
            activity_map,
        ):
            pattern_stops.append(stop)
            auto_sequence += 1

    log.info(
        "Generated flexible pattern stops",
        count=len(pattern_stops),
        vehicle_journey_id=vehicle_journey.id,
        pattern_id=service_pattern.id,
    )

    return pattern_stops
