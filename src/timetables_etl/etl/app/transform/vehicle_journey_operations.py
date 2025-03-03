"""
Functions to Calculate the Operating and Non Operating days for a Vehicle Journey
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence

from common_layer.database.models import (
    TMDayOfWeek,
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
    TransmodelOperatingProfile,
    TransmodelServicedOrganisationVehicleJourney,
    TransmodelVehicleJourney,
)
from common_layer.xml.txc.models import (
    TXCBankHolidayDays,
    TXCBankHolidayOperation,
    TXCDateRange,
    TXCDaysOfWeek,
    TXCOperatingProfile,
    TXCService,
    TXCServicedOrganisationDatePattern,
    TXCSpecialDaysOperation,
    TXCVehicleJourney,
)
from structlog.stdlib import get_logger

from ..load.models_context import OperatingProfileProcessingContext
from .vehicle_journey_operations_serviced_org import (
    create_serviced_organisation_vehicle_journeys,
)

log = get_logger()


@dataclass(frozen=True)
class VehicleJourneyOperations:
    """
    Dataclass to hold processed Vehicle Journey Operations
    That need to be added to the DB
    """

    operating_profiles: list[TransmodelOperatingProfile]
    operating_dates: list[TransmodelOperatingDatesExceptions]
    non_operating_dates: list[TransmodelNonOperatingDatesExceptions]
    serviced_organisation_vehicle_journeys: list[
        TransmodelServicedOrganisationVehicleJourney
    ]
    working_days_patterns: list[
        tuple[
            TransmodelServicedOrganisationVehicleJourney,
            list[TXCServicedOrganisationDatePattern],
        ]
    ]


def create_operating_profiles(
    days: TXCDaysOfWeek,
    vehicle_journey: TransmodelVehicleJourney,
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
            day_of_week=day, vehicle_journey_id=vehicle_journey.id
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


def process_special_operating_days(
    operations: TXCSpecialDaysOperation | None,
    vehicle_journey: TransmodelVehicleJourney,
) -> tuple[
    list[TransmodelOperatingDatesExceptions],
    list[TransmodelNonOperatingDatesExceptions],
]:
    """
    Generate Special Operating days
    """

    special_operating_dates = create_operating_dates(
        operations.DaysOfOperation if operations else [], vehicle_journey.id
    )
    special_non_operating_dates = create_non_operating_dates(
        operations.DaysOfNonOperation if operations else [], vehicle_journey.id
    )
    log.info(
        "Special Operating Dates Calculated",
        operating_count=len(special_operating_dates),
        non_operating_count=len(special_non_operating_dates),
    )

    return special_operating_dates, special_non_operating_dates


def process_bank_holidays(
    operations: TXCBankHolidayOperation | None,
    bank_holidays: dict[str, list[date]],
    vehicle_journey: TransmodelVehicleJourney,
) -> tuple[
    list[TransmodelOperatingDatesExceptions],
    list[TransmodelNonOperatingDatesExceptions],
]:
    """
    Process bank holiday operations and return operating/non-operating dates
    """
    if operations is None:
        return ([], [])
    operating_dates = get_bank_holiday_dates(operations.DaysOfOperation, bank_holidays)
    non_operating_dates = get_bank_holiday_dates(
        operations.DaysOfNonOperation, bank_holidays
    )
    tm_operating_dates = [
        TransmodelOperatingDatesExceptions(
            operating_date=d, vehicle_journey_id=vehicle_journey.id
        )
        for d in operating_dates
    ]
    tm_non_operating_dates = [
        TransmodelNonOperatingDatesExceptions(
            non_operating_date=d, vehicle_journey_id=vehicle_journey.id
        )
        for d in non_operating_dates
    ]

    log.info(
        "Bank Holiday Operations found for VehicleJourney",
        operating_dates=len(tm_operating_dates),
        non_operating_dates=len(tm_non_operating_dates),
        vehicle_journey_id=vehicle_journey.id,
    )
    return tm_operating_dates, tm_non_operating_dates


def get_operating_profile(
    txc_vj: TXCVehicleJourney, txc_services: list[TXCService]
) -> TXCOperatingProfile | None:
    """
    Retrieves the appropriate OperatingProfile for a vehicle journey following a priority order.
        - Vehicle Journey OperatingProfile
        - Service OperatingProfile
    """
    if txc_vj.OperatingProfile:
        return txc_vj.OperatingProfile

    for service in txc_services:
        if service.OperatingProfile:
            log.info(
                "Using Service OperatingProfile as VJ OperatingProfile not found",
                txc_vj_id=txc_vj.VehicleJourneyCode,
                service_code=service.ServiceCode,
            )
            return service.OperatingProfile

    log.warning(
        "No OperatingProfile found in VJ or Services",
        txc_vj_id=txc_vj.VehicleJourneyCode,
    )
    return None


def create_vehicle_journey_operations(
    txc_vj: TXCVehicleJourney,
    tm_vj: TransmodelVehicleJourney,
    context: OperatingProfileProcessingContext,
) -> VehicleJourneyOperations:
    """
    Create all operations data for a vehicle journey from TXC data

    - Operating Profile
        - Monday to Friday (HolidaysOnly Ignored)
    - Special Days
    - Bank Holidays
    - Serviced Organisation Operations
    """
    operating_profile = get_operating_profile(txc_vj, context.txc_services)
    if not operating_profile:
        log.warning(
            (
                "TXC Vehicle Journey and Servicemissing OperatingProfile, "
                "returning No dates of operation"
            ),
            txc_vj_id=txc_vj.VehicleJourneyCode,
            tm_vj_id=tm_vj,
        )
        return VehicleJourneyOperations([], [], [], [], [])

    special_operating_dates, special_non_operating_dates = (
        process_special_operating_days(operating_profile.SpecialDaysOperation, tm_vj)
    )
    bank_holiday_operating_dates, bank_holiday_non_operating_dates = (
        process_bank_holidays(
            operating_profile.BankHolidayOperation,
            context.bank_holidays,
            tm_vj,
        )
    )
    log.critical("OperatingProfile", operating_profile=operating_profile)
    serviced_org_vehicle_journeys, working_days_patterns = (
        create_serviced_organisation_vehicle_journeys(
            operating_profile.ServicedOrganisationDayType,
            tm_vj,
            context.tm_serviced_orgs,
            context.txc_serviced_orgs_dict,
        )
    )

    result = VehicleJourneyOperations(
        operating_profiles=create_operating_profiles(
            operating_profile.RegularDayType, tm_vj
        ),
        operating_dates=[*special_operating_dates, *bank_holiday_operating_dates],
        non_operating_dates=[
            *special_non_operating_dates,
            *bank_holiday_non_operating_dates,
        ],
        serviced_organisation_vehicle_journeys=serviced_org_vehicle_journeys,
        working_days_patterns=working_days_patterns,
    )
    log.info(
        "Generated Vehicle Journey Operations",
        operating_profiles=len(result.operating_profiles),
        operating_dates=len(result.operating_dates),
        non_operating_dates=len(result.non_operating_dates),
        serviced_org_vehicle_journeys=len(
            result.serviced_organisation_vehicle_journeys
        ),
        working_days_patterns=len(result.working_days_patterns),
        vehicle_journey_id=tm_vj.id,
    )
    return result
