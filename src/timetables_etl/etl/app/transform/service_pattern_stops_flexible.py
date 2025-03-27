"""
Flexible Service Pattern Stop Handling
"""

from dataclasses import dataclass
from typing import Sequence

from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelVehicleJourney,
)
from common_layer.xml.txc.helpers.service import get_stop_activity_details
from common_layer.xml.txc.models import (
    TXCFixedStopUsage,
    TXCFlexibleJourneyPattern,
    TXCFlexibleStopUsage,
)
from structlog.stdlib import get_logger

log = get_logger()


@dataclass
class FlexibleStopContext:
    """Context for creating a service pattern stop"""

    sequence_number: int
    service_pattern: TransmodelServicePattern
    vehicle_journey: TransmodelVehicleJourney


@dataclass
class StopDetails:
    """Details for a service pattern stop"""

    stop_ref: str
    naptan_stop: NaptanStopPoint | None
    is_timing_point: bool
    activity_id: int


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
    details: StopDetails,
    context: FlexibleStopContext,
) -> TransmodelServicePatternStop:
    """
    Create a service pattern stop for flexible services
    Flexible Services don't have departure times
    """
    return TransmodelServicePatternStop(
        sequence_number=context.sequence_number,
        atco_code=details.stop_ref,
        naptan_stop_id=details.naptan_stop.id if details.naptan_stop else None,
        service_pattern_id=context.service_pattern.id,
        departure_time=None,
        is_timing_point=details.is_timing_point,
        txc_common_name=(
            details.naptan_stop.common_name if details.naptan_stop else None
        ),
        vehicle_journey_id=context.vehicle_journey.id,
        stop_activity_id=details.activity_id,
        auto_sequence_number=context.sequence_number,
    )


def process_sequence_stop(
    stop_point: TXCFixedStopUsage | TXCFlexibleStopUsage,
    stop_sequence: Sequence[NaptanStopPoint],
    context: FlexibleStopContext,
    stop_activity_id_map: dict[str, int],
) -> TransmodelServicePatternStop | None:
    """Process a single stop in the sequence"""
    naptan_stop = find_naptan_stop(stop_point.StopPointRef, stop_sequence)
    if not naptan_stop:
        return None

    try:
        is_timing_point, activity_type = get_stop_activity_details(stop_point)
    except ValueError as e:
        log.warning(
            "Unknown stop type",
            error=str(e),
            vehicle_journey_id=context.vehicle_journey.id,
        )
        return None

    activity_id = stop_activity_id_map.get(activity_type)
    if not activity_id:
        log.error(
            "Stop activity not found - skipping stop",
            requested_activity=activity_type,
            available_activities=list(stop_activity_id_map.keys()),
            stop_point=stop_point.StopPointRef,
            vehicle_journey_id=context.vehicle_journey.id,
        )
        return None

    details = StopDetails(
        stop_ref=stop_point.StopPointRef,
        naptan_stop=naptan_stop,
        is_timing_point=is_timing_point,
        activity_id=activity_id,
    )

    return create_flexible_stop(details, context)


def generate_flexible_pattern_stops(
    service_pattern: TransmodelServicePattern,
    vehicle_journey: TransmodelVehicleJourney,
    flexible_pattern: TXCFlexibleJourneyPattern,
    stop_sequence: Sequence[NaptanStopPoint],
    stop_activity_id_map: dict[str, int],
) -> list[TransmodelServicePatternStop]:
    """Generate service pattern stops for a flexible service"""
    log.info(
        "Starting flexible pattern stops generation",
        stop_count=len(stop_sequence),
        activity_count=len(stop_activity_id_map),
        pattern_id=flexible_pattern.id,
    )

    pattern_stops: list[TransmodelServicePatternStop] = []
    auto_sequence: int = 0

    # Process main sequence stops
    for stop_point in flexible_pattern.StopPointsInSequence:
        context = FlexibleStopContext(
            service_pattern=service_pattern,
            vehicle_journey=vehicle_journey,
            sequence_number=auto_sequence,
        )

        if stop := process_sequence_stop(
            stop_point,
            stop_sequence,
            context,
            stop_activity_id_map,
        ):
            pattern_stops.append(stop)
            auto_sequence += 1

    # Process flexible zones
    for zone in flexible_pattern.FlexibleZones:
        context = FlexibleStopContext(
            service_pattern=service_pattern,
            vehicle_journey=vehicle_journey,
            sequence_number=auto_sequence,
        )

        if stop := process_sequence_stop(
            zone,
            stop_sequence,
            context,
            stop_activity_id_map,
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
