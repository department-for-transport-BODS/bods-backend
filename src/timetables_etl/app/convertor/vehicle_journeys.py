"""
Pydantic Model to Transmodel for Vehicle Journeys
"""

from timetables_etl.app.database.models.model_transmodel import TransmodelVehicleJourney
from timetables_etl.app.txc.models.txc_vehicle_journey import TXCVehicleJourney

from .utils import parse_departure_time


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
