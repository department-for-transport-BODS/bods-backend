"""
Pydantic Model to Transmodel for Vehicle Journeys
"""

from datetime import time
from typing import cast

from structlog.stdlib import get_logger

from ..database.models import (
    TransmodelFlexibleServiceOperationPeriod,
    TransmodelServicePattern,
    TransmodelVehicleJourney,
)
from ..txc.models import (
    TXCFlexibleJourneyPattern,
    TXCFlexibleServiceTimes,
    TXCFlexibleVehicleJourney,
    TXCJourneyPattern,
    TXCVehicleJourney,
)

log = get_logger()


def create_vehicle_journey(
    vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
    pattern: TransmodelServicePattern,
    jp: TXCJourneyPattern | TXCFlexibleJourneyPattern,
) -> TransmodelVehicleJourney:
    """
    Create a Transmodel Vehicle Journey
    """
    ticket_machine = (
        vehicle_journey.Operational.TicketMachine
        if vehicle_journey.Operational
        else None
    )
    block = vehicle_journey.Operational.Block if vehicle_journey.Operational else None

    match vehicle_journey:
        case TXCVehicleJourney():
            departure_time = cast(time, vehicle_journey.DepartureTime)
            departure_day_shift = bool(vehicle_journey.DepartureDayShift)
        case TXCFlexibleVehicleJourney():
            departure_time = None
            departure_day_shift = False
        case _:
            raise ValueError(f"Unknown vehicle journey type: {type(vehicle_journey)}")

    return TransmodelVehicleJourney(
        start_time=departure_time,
        direction=jp.Direction,
        journey_code=ticket_machine.JourneyCode if ticket_machine else None,
        line_ref=vehicle_journey.LineRef,
        departure_day_shift=departure_day_shift,
        service_pattern_id=pattern.id,
        block_number=block.BlockNumber if block else None,
    )


def generate_pattern_vehicle_journeys(
    txc_vjs: list[TXCVehicleJourney | TXCFlexibleVehicleJourney],
    txc_jp: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    tm_service_pattern: TransmodelServicePattern,
) -> list[
    tuple[TransmodelVehicleJourney, TXCVehicleJourney | TXCFlexibleVehicleJourney]
]:
    """
    Generate vehicle journeys for a service pattern
    """
    if not txc_jp.id:
        raise ValueError("Journey pattern must have an ID")

    if not tm_service_pattern.id:
        raise ValueError("Service pattern must have an ID")

    # Filter and validate vehicle journeys for this pattern
    pattern_journeys = [vj for vj in txc_vjs if vj.JourneyPatternRef == txc_jp.id]

    if not pattern_journeys:
        log.warning(
            "No valid vehicle journeys found for pattern",
            pattern_id=txc_jp.id,
            total_journeys=len(txc_vjs),
        )
        return []

    results: list[
        tuple[TransmodelVehicleJourney, TXCVehicleJourney | TXCFlexibleVehicleJourney]
    ] = []

    for vj in pattern_journeys:
        log.debug("Processing Vehicle Journey 🌷", vj_id=vj.VehicleJourneyCode)
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
        pattern_type=(
            "flexible" if isinstance(txc_jp, TXCFlexibleJourneyPattern) else "standard"
        ),
        attempted=len(pattern_journeys),
        succeeded=len(results),
    )

    return results


def generate_flexible_service_operation_period(
    tm_vj: TransmodelVehicleJourney,
    txc_vj: TXCFlexibleVehicleJourney,
) -> list[TransmodelFlexibleServiceOperationPeriod]:
    """
    Generate operations period for a flexdible Service
    """
    midnight = time(0, 0, 0)
    end_of_day = time(23, 59, 59)

    operation_periods: list[TransmodelFlexibleServiceOperationPeriod] = []
    log.debug(
        "Generating Flexible Service VKJ Operation Periods",
        transmodel_vj_id=tm_vj.id,
        txc_vj_id=txc_vj.VehicleJourneyCode,
    )
    for service_time in txc_vj.FlexibleServiceTimes:
        match service_time:
            case TXCFlexibleServiceTimes(AllDayService=True):
                operation_periods.append(
                    TransmodelFlexibleServiceOperationPeriod(
                        vehicle_journey_id=tm_vj.id,
                        start_time=midnight,
                        end_time=end_of_day,
                    )
                )
            case TXCFlexibleServiceTimes(ServicePeriod=period) if period:
                try:
                    operation_periods.append(
                        TransmodelFlexibleServiceOperationPeriod(
                            vehicle_journey_id=tm_vj.id,
                            start_time=time.fromisoformat(period.StartTime),
                            end_time=time.fromisoformat(period.EndTime),
                        )
                    )
                except ValueError as e:
                    raise ValueError(
                        f"Wrong time format in ServicePeriod: {period.StartTime} - {period.EndTime}"
                    ) from e
    return operation_periods
