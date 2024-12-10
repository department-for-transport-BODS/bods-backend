"""
Functions to Calculate the Operating and Non Operating days for a Vehicle Journey
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence

from structlog.stdlib import get_logger

from timetables_etl.etl.app.database.models.model_transmodel import (
    TMDayOfWeek,
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
    TransmodelOperatingProfile,
)
from timetables_etl.etl.app.txc.models import (
    TXCDateRange,
    TXCDaysOfWeek,
    TXCVehicleJourney,
)
from timetables_etl.etl.app.txc.models.txc_vehicle_journey import (
    TXCBankHolidayDays,
    TXCBankHolidayOperation,
)

log = get_logger()


@dataclass(frozen=True)
class VehicleJourneyOperations:
    """
    Container for vehicle journey operating data
    """

    operating_profiles: list[TransmodelOperatingProfile]
    operating_dates: list[TransmodelOperatingDatesExceptions]
    non_operating_dates: list[TransmodelNonOperatingDatesExceptions]


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


def get_bank_holiday_dates(
    holiday_days: TXCBankHolidayDays, bank_holidays: dict[str, list[date]]
) -> list[date]:
    """
    Get list of dates for enabled bank holidays
    """
    dates: list[date] = []

    for holiday_name, is_active in holiday_days:
        if is_active and holiday_name in bank_holidays:
            dates.extend(bank_holidays[holiday_name])

    return sorted(dates)


def process_bank_holidays(
    bank_holiday_op: TXCBankHolidayOperation,
    bank_holidays: dict[str, list[date]],
    vehicle_journey_id: int,
) -> tuple[
    list[TransmodelOperatingDatesExceptions],
    list[TransmodelNonOperatingDatesExceptions],
]:
    """Process bank holiday operations and return operating/non-operating dates"""
    log.error("Proccesssing bank holidays", vehicle_journey_id=vehicle_journey_id)
    operating_dates = get_bank_holiday_dates(
        bank_holiday_op.DaysOfOperation, bank_holidays
    )
    non_operating_dates = get_bank_holiday_dates(
        bank_holiday_op.DaysOfNonOperation, bank_holidays
    )
    tm_operating_dates = [
        TransmodelOperatingDatesExceptions(
            operating_date=d, vehicle_journey_id=vehicle_journey_id
        )
        for d in operating_dates
    ]
    tm_non_operating_dates = [
        TransmodelNonOperatingDatesExceptions(
            non_operating_date=d, vehicle_journey_id=vehicle_journey_id
        )
        for d in non_operating_dates
    ]

    log.info(
        "Bank Holiday Operations found for VehicleJourney",
        operating_dates=len(tm_operating_dates),
        non_operating_dates=len(tm_non_operating_dates),
        vehicle_journey_id=vehicle_journey_id,
    )
    return tm_operating_dates, tm_non_operating_dates


def create_vehicle_journey_operations(
    txc_vj: TXCVehicleJourney,
    vehicle_journey_id: int,
    bank_holidays: dict[str, list[date]],
) -> VehicleJourneyOperations:
    """
    Create all operations data for a vehicle journey from TXC data

    - Operating Profile
        - Monday to Friday (HolidaysOnly Ignored)
    - Special Days
    - Bank Holidays
    """
    if not txc_vj.OperatingProfile:
        log.warning(
            "TXC Vehicle Journey missing OperatingProfile, returning No dates of operation",
            txc_vj_id=txc_vj.VehicleJourneyCode,
            tm_vj_id=vehicle_journey_id,
        )
        return VehicleJourneyOperations([], [], [])

    log.critical("Data", profile=txc_vj.OperatingProfile, bank_holidays=bank_holidays)
    operating_profile = txc_vj.OperatingProfile
    special_days = operating_profile.SpecialDaysOperation

    special_operating_dates = create_operating_dates(
        special_days.DaysOfOperation if special_days else [], vehicle_journey_id
    )
    special_non_operating_dates = create_non_operating_dates(
        special_days.DaysOfNonOperation if special_days else [], vehicle_journey_id
    )

    bank_holiday_operating_dates, bank_holiday_non_operating_dates = (
        process_bank_holidays(
            operating_profile.BankHolidayOperation, bank_holidays, vehicle_journey_id
        )
        if operating_profile.BankHolidayOperation
        else ([], [])
    )
    result = VehicleJourneyOperations(
        operating_profiles=create_operating_profiles(
            operating_profile.RegularDayType, vehicle_journey_id
        ),
        operating_dates=[*special_operating_dates, *bank_holiday_operating_dates],
        non_operating_dates=[
            *special_non_operating_dates,
            *bank_holiday_non_operating_dates,
        ],
    )
    log.info(
        "Generated Vehicle Journey Operations",
        operating_profiles=len(result.operating_profiles),
        operating_dates=len(result.operating_dates),
        non_operating_dates=len(result.non_operating_dates),
        vehicle_journey_id=vehicle_journey_id,
    )
    return result
