"""
Serviced Org Vehicle Journey Processing
"""

from common_layer.database.models import (
    TransmodelServicedOrganisationVehicleJourney,
    TransmodelServicedOrganisationWorkingDays,
    TransmodelVehicleJourney,
)
from common_layer.xml.txc.models import (
    TXCServicedOrganisation,
    TXCServicedOrganisationDatePattern,
    TXCServicedOrganisationDays,
    TXCServicedOrganisationDayType,
)
from structlog.stdlib import get_logger

from ..helpers import ServicedOrgLookup

log = get_logger()


def create_serviced_org_vehicle_journey(
    org_ref: str,
    operating_on_working_days: bool,
    vehicle_journey: TransmodelVehicleJourney,
    serviced_orgs: ServicedOrgLookup,
) -> TransmodelServicedOrganisationVehicleJourney:
    """
    Create a single serviced organisation vehicle journey record
    """
    return TransmodelServicedOrganisationVehicleJourney(
        operating_on_working_days=operating_on_working_days,
        serviced_organisation_id=serviced_orgs[org_ref].id,
        vehicle_journey_id=vehicle_journey.id,
    )


def process_org_ref(
    org_ref: str,
    operating_on_working_days: bool,
    vehicle_journey: TransmodelVehicleJourney,
    serviced_orgs: ServicedOrgLookup,
    txc_serviced_orgs: dict[str, TXCServicedOrganisation],
) -> tuple[
    TransmodelServicedOrganisationVehicleJourney | None,
    list[TXCServicedOrganisationDatePattern],
]:
    """
    Process a single organisation reference and create a vehicle journey record if valid
    Returns the created vehicle journey record and any associated working day patterns
    """
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
        return None, []

    so_vj = create_serviced_org_vehicle_journey(
        org_ref=org_ref,
        operating_on_working_days=operating_on_working_days,
        vehicle_journey=vehicle_journey,
        serviced_orgs=serviced_orgs,
    )

    working_days = txc_org.WorkingDays or []

    return so_vj, working_days


def process_days_element(
    days: TXCServicedOrganisationDays,
    is_operation_day: bool,
    vehicle_journey: TransmodelVehicleJourney,
    serviced_orgs: ServicedOrgLookup,
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
    Process a single TXCServicedOrganisationDays element
    Returns for both operation and non-operation days:
        - vehicle journey records
        - working days patterns

    """
    vehicle_journey_records: list[TransmodelServicedOrganisationVehicleJourney] = []
    working_days_patterns: list[
        tuple[
            TransmodelServicedOrganisationVehicleJourney,
            list[TXCServicedOrganisationDatePattern],
        ]
    ] = []
    day_type = "DaysOfOperation" if is_operation_day else "DaysOfNonOperation"

    if days.WorkingDays:
        log.debug(
            "Processing serviced organisation working day refs",
            day_type=day_type,
            working_day_refs=days.WorkingDays,
            vehicle_journey_id=vehicle_journey.id,
        )

        # For operation days: operating_on_working_days=True (operates ON working days)
        # For non-operation days: operating_on_working_days=False (does NOT operate on working days)
        working_days_flag = is_operation_day

        for org_ref in days.WorkingDays:
            so_vj, working_days = process_org_ref(
                org_ref=org_ref,
                operating_on_working_days=working_days_flag,
                vehicle_journey=vehicle_journey,
                serviced_orgs=serviced_orgs,
                txc_serviced_orgs=txc_serviced_orgs,
            )

            if so_vj:
                vehicle_journey_records.append(so_vj)
                # Add working days patterns for both operation and non-operation days
                if working_days:
                    working_days_patterns.append((so_vj, working_days))

    if days.Holidays:
        log.debug(
            "Processing serviced organisation holiday refs",
            day_type=day_type,
            holiday_refs=days.Holidays,
            vehicle_journey_id=vehicle_journey.id,
        )

        # For operation days: operating_on_working_days=False (operates ON holidays)
        # For non-operation days: operating_on_working_days=True (does NOT operate on holidays)
        holiday_flag = not is_operation_day

        for org_ref in days.Holidays:
            so_vj, working_days = process_org_ref(
                org_ref=org_ref,
                operating_on_working_days=holiday_flag,
                vehicle_journey=vehicle_journey,
                serviced_orgs=serviced_orgs,
                txc_serviced_orgs=txc_serviced_orgs,
            )

            if so_vj:
                vehicle_journey_records.append(so_vj)
                # Add working days patterns for holidays too if available
                if working_days:
                    working_days_patterns.append((so_vj, working_days))

    return vehicle_journey_records, working_days_patterns


def create_serviced_organisation_vehicle_journeys(
    serviced_org_day_type: TXCServicedOrganisationDayType | None,
    vehicle_journey: TransmodelVehicleJourney,
    serviced_orgs: ServicedOrgLookup,
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

    all_vehicle_journey_records: list[TransmodelServicedOrganisationVehicleJourney] = []
    all_working_days_patterns: list[
        tuple[
            TransmodelServicedOrganisationVehicleJourney,
            list[TXCServicedOrganisationDatePattern],
        ]
    ] = []

    for days in serviced_org_day_type.DaysOfOperation:
        vj_records, working_patterns = process_days_element(
            days=days,
            is_operation_day=True,
            vehicle_journey=vehicle_journey,
            serviced_orgs=serviced_orgs,
            txc_serviced_orgs=txc_serviced_orgs,
        )
        all_vehicle_journey_records.extend(vj_records)
        all_working_days_patterns.extend(working_patterns)

    for days in serviced_org_day_type.DaysOfNonOperation:
        vj_records, working_patterns = process_days_element(
            days=days,
            is_operation_day=False,
            vehicle_journey=vehicle_journey,
            serviced_orgs=serviced_orgs,
            txc_serviced_orgs=txc_serviced_orgs,
        )
        all_vehicle_journey_records.extend(vj_records)
        all_working_days_patterns.extend(working_patterns)

    log.info(
        "Generated Serviced Organisation records",
        vehicle_journey_records=len(all_vehicle_journey_records),
        working_days_patterns=len(all_working_days_patterns),
        vehicle_journey_id=vehicle_journey.id,
    )

    return all_vehicle_journey_records, all_working_days_patterns


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
