"""
Functions to Calculate the Operating and Non Operating days for a Vehicle Journey
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence

from structlog.stdlib import get_logger

from ..database.models import (
    TMDayOfWeek,
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
    TransmodelOperatingProfile,
    TransmodelServicedOrganisations,
    TransmodelServicedOrganisationVehicleJourney,
    TransmodelServicedOrganisationWorkingDays,
    TransmodelVehicleJourney,
)
from ..txc.models import TXCDateRange, TXCDaysOfWeek, TXCVehicleJourney
from ..txc.models.txc_serviced_organisation import (
    TXCServicedOrganisation,
    TXCServicedOrganisationDatePattern,
)
from ..txc.models.txc_vehicle_journey import (
    TXCBankHolidayDays,
    TXCBankHolidayOperation,
    TXCServicedOrganisationDayType,
    TXCSpecialDaysOperation,
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


def create_serviced_organisation_working_days(
    so_vj: TransmodelServicedOrganisationVehicleJourney,
    working_day_patterns: list[TXCServicedOrganisationDatePattern],
) -> list[TransmodelServicedOrganisationWorkingDays]:
    """
    Create working days records for a serviced organisation vehicle journey
    """
    working_days_records: list[TransmodelServicedOrganisationWorkingDays] = []

    for date_pattern in working_day_patterns:
        working_days_records.append(
            TransmodelServicedOrganisationWorkingDays(
                start_date=date_pattern.StartDate,
                end_date=date_pattern.EndDate,
                serviced_organisation_vehicle_journey_id=so_vj.id,
            )
        )

    log.debug(
        "Generated working days records for serviced organisation",
        record_count=len(working_days_records),
        date_patterns=len(working_day_patterns),
        so_vj_id=so_vj.id,
    )

    return working_days_records


def create_serviced_org_vehicle_journey(
    org_ref: str,
    operating_on_working_days: bool,
    vehicle_journey: TransmodelVehicleJourney,
    serviced_orgs: dict[str, TransmodelServicedOrganisations],
) -> TransmodelServicedOrganisationVehicleJourney:
    """
    Create a single serviced organisation vehicle journey record
    """
    return TransmodelServicedOrganisationVehicleJourney(
        operating_on_working_days=operating_on_working_days,
        serviced_organisation_id=serviced_orgs[org_ref].id,
        vehicle_journey_id=vehicle_journey.id,
    )


def create_serviced_organisation_vehicle_journeys(
    serviced_org_day_type: TXCServicedOrganisationDayType | None,
    vehicle_journey: TransmodelVehicleJourney,
    serviced_orgs: dict[str, TransmodelServicedOrganisations],
    txc_serviced_orgs: dict[str, TXCServicedOrganisation],
) -> tuple[
    list[TransmodelServicedOrganisationVehicleJourney],
    list[
        tuple[
            TransmodelServicedOrganisationVehicleJourney,
            list[TXCServicedOrganisationDatePattern],
        ]
    ],
]:
    """
    Create serviced organisation vehicle journey records and collect working day patterns to process
    Returns vehicle journey records and a mapping of vehicle journeys to their working day patterns
    """
    if not serviced_org_day_type:
        return [], []

    vehicle_journey_records: list[TransmodelServicedOrganisationVehicleJourney] = []
    working_days_patterns: list[
        tuple[
            TransmodelServicedOrganisationVehicleJourney,
            list[TXCServicedOrganisationDatePattern],
        ]
    ] = []

    if serviced_org_day_type.WorkingDays or serviced_org_day_type.Holidays:
        log.debug(
            "Processing serviced organisation refs",
            working_day_refs=serviced_org_day_type.WorkingDays,
            holiday_refs=serviced_org_day_type.Holidays,
        )

    # Handle working days
    if serviced_org_day_type.WorkingDays:
        for org_ref in serviced_org_day_type.WorkingDays:
            tm_org = serviced_orgs.get(org_ref)
            txc_org = txc_serviced_orgs.get(org_ref)

            if not tm_org or not txc_org:
                log.warning(
                    "Serviced organisation ref not found in lookup tables",
                    org_ref=org_ref,
                    in_tm=org_ref in serviced_orgs,
                    in_txc=org_ref in txc_serviced_orgs,
                    vehicle_journey_id=vehicle_journey.id,
                )
                continue

            so_vj = create_serviced_org_vehicle_journey(
                org_ref=org_ref,
                operating_on_working_days=True,
                vehicle_journey=vehicle_journey,
                serviced_orgs=serviced_orgs,
            )
            vehicle_journey_records.append(so_vj)

            if txc_org.WorkingDays:
                working_days_patterns.append((so_vj, txc_org.WorkingDays))

    # Handle holidays
    if serviced_org_day_type.Holidays:
        for org_ref in serviced_org_day_type.Holidays:
            tm_org = serviced_orgs.get(org_ref)
            txc_org = txc_serviced_orgs.get(org_ref)

            if not tm_org or not txc_org:
                log.warning(
                    "Serviced organisation ref not found in lookup tables",
                    org_ref=org_ref,
                    in_tm=org_ref in serviced_orgs,
                    in_txc=org_ref in txc_serviced_orgs,
                    vehicle_journey_id=vehicle_journey.id,
                )
                continue

            so_vj = create_serviced_org_vehicle_journey(
                org_ref=org_ref,
                operating_on_working_days=False,
                vehicle_journey=vehicle_journey,
                serviced_orgs=serviced_orgs,
            )
            vehicle_journey_records.append(so_vj)

    log.info(
        "Generated Serviced Organisation records",
        vehicle_journey_records=len(vehicle_journey_records),
        working_days_patterns=len(working_days_patterns),
        vehicle_journey_id=vehicle_journey.id,
    )

    return vehicle_journey_records, working_days_patterns


def create_vehicle_journey_operations(
    txc_vj: TXCVehicleJourney,
    tm_vj: TransmodelVehicleJourney,
    txc_serviced_orgs: dict[str, TXCServicedOrganisation],
    tm_serviced_orgs: dict[str, TransmodelServicedOrganisations],
    bank_holidays: dict[str, list[date]],
) -> VehicleJourneyOperations:
    """
    Create all operations data for a vehicle journey from TXC data

    - Operating Profile
        - Monday to Friday (HolidaysOnly Ignored)
    - Special Days
    - Bank Holidays
    - Serviced Organisation Operations
    """
    if not txc_vj.OperatingProfile:
        log.warning(
            "TXC Vehicle Journey missing OperatingProfile, returning No dates of operation",
            txc_vj_id=txc_vj.VehicleJourneyCode,
            tm_vj_id=tm_vj,
        )
        return VehicleJourneyOperations([], [], [], [], [])

    special_operating_dates, special_non_operating_dates = (
        process_special_operating_days(
            txc_vj.OperatingProfile.SpecialDaysOperation, tm_vj
        )
    )
    bank_holiday_operating_dates, bank_holiday_non_operating_dates = (
        process_bank_holidays(
            txc_vj.OperatingProfile.BankHolidayOperation,
            bank_holidays,
            tm_vj,
        )
    )

    serviced_org_vehicle_journeys, working_days_patterns = (
        create_serviced_organisation_vehicle_journeys(
            txc_vj.OperatingProfile.ServicedOrganisationDayType,
            tm_vj,
            tm_serviced_orgs,
            txc_serviced_orgs,
        )
    )

    result = VehicleJourneyOperations(
        operating_profiles=create_operating_profiles(
            txc_vj.OperatingProfile.RegularDayType, tm_vj
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
