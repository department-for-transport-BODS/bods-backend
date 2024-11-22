"""
Pydantic Model to Transmodel for Vehicle Journeys
"""

from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import Sequence, cast

from structlog.stdlib import get_logger

from timetables_etl.app.database.models.model_transmodel import (
    TMDayOfWeek,
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
    TransmodelOperatingProfile,
    TransmodelServicePattern,
    TransmodelVehicleJourney,
)
from timetables_etl.app.txc.models.txc_service import TXCJourneyPattern
from timetables_etl.app.txc.models.txc_vehicle_journey import (
    TXCDateRange,
    TXCDaysOfWeek,
    TXCVehicleJourney,
)

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


def create_operating_profiles(
    days: TXCDaysOfWeek, vehicle_journey_id: int
) -> list[TransmodelOperatingProfile]:
    """
    Convert TXCDaysOfWeek to operating profile records
    """
    day_mappings = {
        TMDayOfWeek.MONDAY: days.Monday,
        TMDayOfWeek.TUESDAY: days.Tuesday,
        TMDayOfWeek.WEDNESDAY: days.Wednesday,
        TMDayOfWeek.THURSDAY: days.Thursday,
        TMDayOfWeek.FRIDAY: days.Friday,
        TMDayOfWeek.SATURDAY: days.Saturday,
        TMDayOfWeek.SUNDAY: days.Sunday,
    }

    return [
        TransmodelOperatingProfile(
            day_of_week=day, vehicle_journey_id=vehicle_journey_id
        )
        for day, enabled in day_mappings.items()
        if enabled
    ]


def generate_dates(start_date: date, end_date: date) -> list[date]:
    """
    Generate a list of dates between start and end dates inclusive

    """
    days_between = (end_date - start_date).days + 1
    return [start_date + timedelta(days=x) for x in range(days_between)]


def create_operating_dates(
    date_ranges: Sequence[TXCDateRange], vehicle_journey_id: int
) -> list[TransmodelOperatingDatesExceptions]:
    """
    Create operating dates exceptions from date ranges
    """
    return [
        TransmodelOperatingDatesExceptions(
            operating_date=current_date, vehicle_journey_id=vehicle_journey_id
        )
        for date_range in date_ranges
        for current_date in generate_dates(date_range.StartDate, date_range.EndDate)
    ]


def create_non_operating_dates(
    date_ranges: Sequence[TXCDateRange], vehicle_journey_id: int
) -> list[TransmodelNonOperatingDatesExceptions]:
    """
    Create non-operating dates exceptions from date ranges
    """
    return [
        TransmodelNonOperatingDatesExceptions(
            non_operating_date=current_date, vehicle_journey_id=vehicle_journey_id
        )
        for date_range in date_ranges
        for current_date in generate_dates(date_range.StartDate, date_range.EndDate)
    ]


@dataclass(frozen=True)
class VehicleJourneyOperations:
    """
    Container for vehicle journey operating data
    """

    operating_profiles: list[TransmodelOperatingProfile]
    operating_dates: list[TransmodelOperatingDatesExceptions]
    non_operating_dates: list[TransmodelNonOperatingDatesExceptions]


def create_vehicle_journey_operations(
    txc_journey: TXCVehicleJourney, vehicle_journey_id: int
) -> VehicleJourneyOperations:
    """
    Create all operations data for a vehicle journey from TXC data

    """
    if not txc_journey.OperatingProfile:
        return VehicleJourneyOperations([], [], [])

    operating_profile = txc_journey.OperatingProfile
    special_days = operating_profile.SpecialDaysOperation

    return VehicleJourneyOperations(
        operating_profiles=create_operating_profiles(
            operating_profile.RegularDayType, vehicle_journey_id
        ),
        operating_dates=create_operating_dates(
            special_days.DaysOfOperation if special_days else [], vehicle_journey_id
        ),
        non_operating_dates=create_non_operating_dates(
            special_days.DaysOfNonOperation if special_days else [], vehicle_journey_id
        ),
    )


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
