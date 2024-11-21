"""
Pydantic Model to Transmodel for Vehicle Journeys
"""

from datetime import time
from typing import cast

from structlog.stdlib import get_logger

from timetables_etl.app.database.client import BodsDB
from timetables_etl.app.database.models.model_transmodel import (
    TransmodelServicePattern,
    TransmodelVehicleJourney,
)
from timetables_etl.app.database.repos.repo_transmodel import (
    TransmodelVehicleJourneyRepo,
)
from timetables_etl.app.txc.models.txc_service import TXCJourneyPattern
from timetables_etl.app.txc.models.txc_vehicle_journey import TXCVehicleJourney

from ..txc.helpers.utils import parse_departure_time

log = get_logger()


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


def transform_vehicle_journeys(
    journeys: list[TXCVehicleJourney], service_patterns: dict[str, int] | None = None
) -> list[TransmodelVehicleJourney]:
    """Transform TXC vehicle journeys to Transmodel format"""
    result: list[TransmodelVehicleJourney] = []

    for journey in journeys:
        journey_code = (
            journey.Operational.TicketMachine.JourneyCode
            if journey.Operational and journey.Operational.TicketMachine
            else None
        )

        block_number = (
            journey.Operational.Block.BlockNumber
            if journey.Operational and journey.Operational.Block
            else None
        )

        service_pattern_id = None
        if service_patterns and journey.JourneyPatternRef:
            pattern_key = f"{journey.ServiceRef}-{journey.JourneyPatternRef}"
            service_pattern_id = service_patterns.get(pattern_key)

        result.append(
            TransmodelVehicleJourney(
                start_time=parse_departure_time(journey.DepartureTime),
                journey_code=journey_code,
                line_ref=journey.LineRef,
                direction=None,
                departure_day_shift=bool(journey.DepartureDayShift),
                service_pattern_id=service_pattern_id,
                block_number=block_number,
            )
        )

    return result


def generate_pattern_vehicle_journeys(
    txc_vjs: list[TXCVehicleJourney],
    txc_jp: TXCJourneyPattern,
    tm_service_pattern: TransmodelServicePattern,
) -> list[TransmodelVehicleJourney]:
    """
    Generate vehicle journeys for a service pattern
    """
    # Filter vehicle journeys for this pattern
    pattern_journeys = [vj for vj in txc_vjs if vj.JourneyPatternRef == txc_jp.id]

    journeys = [
        create_vehicle_journey(vj, tm_service_pattern, txc_jp)
        for vj in pattern_journeys
    ]

    log.info(
        "Generated vehicle journeys",
        pattern_id=tm_service_pattern.service_pattern_id,
        count=len(journeys),
    )

    return journeys


def process_service_pattern_vehicle_journeys(
    txc_vjs: list[TXCVehicleJourney],
    txc_jp: TXCJourneyPattern,
    tm_service_pattern: TransmodelServicePattern,
    db: BodsDB,
) -> list[TransmodelVehicleJourney]:
    """
    Generate and save to DB Transmodel Vehicle Journeys for a Service Pattern
    """
    tm_vjs = generate_pattern_vehicle_journeys(txc_vjs, txc_jp, tm_service_pattern)
    results = TransmodelVehicleJourneyRepo(db).bulk_insert(tm_vjs)

    log.info(
        "Saved vehicle journeys",
        pattern_id=results[0].service_pattern_id if results else None,
        count=len(results),
    )

    return results
