"""
Pydantic Model to Transmodel for Vehicle Journeys
"""

from datetime import time
from typing import cast

from structlog.stdlib import get_logger

from ..database.models.model_transmodel import (
    TransmodelServicePattern,
    TransmodelVehicleJourney,
)
from ..txc.models import TXCJourneyPattern, TXCVehicleJourney

log = get_logger()


def _validate_vehicle_journey(vj: TXCVehicleJourney) -> bool:
    """
    Validate required fields on vehicle journey
    """
    required_fields = {
        "VehicleJourneyCode": vj.VehicleJourneyCode,
        "JourneyPatternRef": vj.JourneyPatternRef,
        "DepartureTime": vj.DepartureTime,
        "LineRef": vj.LineRef,
    }

    is_valid = all(required_fields.values())

    if not is_valid:
        missing_fields = [k for k, v in required_fields.items() if not v]
        log.warning(
            "Invalid vehicle journey",
            journey_id=vj.VehicleJourneyCode,
            missing_fields=missing_fields,
        )

    return is_valid


def create_vehicle_journey(
    vehicle_journey: TXCVehicleJourney,
    pattern: TransmodelServicePattern,
    jp: TXCJourneyPattern,
) -> TransmodelVehicleJourney:
    """Create a single vehicle journey"""
    ticket_machine = (
        vehicle_journey.Operational.TicketMachine
        if vehicle_journey.Operational
        else None
    )
    block = vehicle_journey.Operational.Block if vehicle_journey.Operational else None

    departure_time = cast(time, vehicle_journey.DepartureTime)

    return TransmodelVehicleJourney(
        start_time=departure_time,
        direction=jp.Direction,
        journey_code=ticket_machine.JourneyCode if ticket_machine else None,
        line_ref=vehicle_journey.LineRef,
        departure_day_shift=bool(vehicle_journey.DepartureDayShift),
        service_pattern_id=pattern.id,
        block_number=block.BlockNumber if block else None,
    )


def generate_pattern_vehicle_journeys(
    txc_vjs: list[TXCVehicleJourney],
    txc_jp: TXCJourneyPattern,
    tm_service_pattern: TransmodelServicePattern,
) -> list[tuple[TransmodelVehicleJourney, TXCVehicleJourney]]:
    """
    Generate vehicle journeys for a service pattern
    """
    if not txc_jp.id:
        raise ValueError("Journey pattern must have an ID")

    if not tm_service_pattern.id:
        raise ValueError("Service pattern must have an ID")

    # Filter and validate vehicle journeys for this pattern
    pattern_journeys = [
        vj
        for vj in txc_vjs
        if vj.JourneyPatternRef == txc_jp.id and _validate_vehicle_journey(vj)
    ]

    if not pattern_journeys:
        log.warning(
            "No valid vehicle journeys found for pattern",
            pattern_id=txc_jp.id,
            total_journeys=len(txc_vjs),
        )
        return []

    results: list[tuple[TransmodelVehicleJourney, TXCVehicleJourney]] = []

    for vj in pattern_journeys:
        try:
            tm_journey = create_vehicle_journey(vj, tm_service_pattern, txc_jp)
            results.append((tm_journey, vj))
        except Exception as e:
            log.error(
                "Failed to create vehicle journey",
                error=str(e),
                journey_id=vj.VehicleJourneyCode,
                pattern_id=txc_jp.id,
            )
            continue

    log.info(
        "Generated vehicle journeys",
        pattern_id=tm_service_pattern.id,
        attempted=len(pattern_journeys),
        succeeded=len(results),
    )

    return results
