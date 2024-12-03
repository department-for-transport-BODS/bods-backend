"""
transmodel_vehiclejourny Operating profiles generation
"""

from datetime import date

from structlog.stdlib import get_logger

from ..database.client import BodsDB
from ..database.models import TransmodelServicedOrganisationWorkingDays
from ..database.models.model_transmodel_vehicle_journey import TransmodelVehicleJourney
from ..database.repos import (
    TransmodelServicedOrganisationVehicleJourneyRepo,
    TransmodelServicedOrganisationWorkingDaysRepo,
)
from ..database.repos.repo_transmodel_vehicle_journey import (
    TransmodelNonOperatingDatesExceptionsRepo,
    TransmodelOperatingDatesExceptionsRepo,
    TransmodelOperatingProfileRepo,
)
from ..helpers import ServicedOrgLookup
from ..transform.vehicle_journey_operations import (
    create_serviced_organisation_working_days,
    create_vehicle_journey_operations,
)
from ..txc.models import TXCServicedOrganisation, TXCVehicleJourney

log = get_logger()


def process_operating_profile(
    tm_vj: TransmodelVehicleJourney,
    txc_vj: TXCVehicleJourney,
    txc_serviced_orgs_dict: dict[str, TXCServicedOrganisation],
    bank_holidays: dict[str, list[date]],
    tm_serviced_orgs: ServicedOrgLookup,
    db: BodsDB,
):
    """
    Process a single Operating Profile
    """
    operations = create_vehicle_journey_operations(
        txc_vj=txc_vj,
        tm_vj=tm_vj,
        bank_holidays=bank_holidays,
        tm_serviced_orgs=tm_serviced_orgs,
        txc_serviced_orgs=txc_serviced_orgs_dict,
    )

    if operations.operating_profiles:
        TransmodelOperatingProfileRepo(db).bulk_insert(operations.operating_profiles)

    if operations.operating_dates:
        TransmodelOperatingDatesExceptionsRepo(db).bulk_insert(
            operations.operating_dates
        )

    if operations.non_operating_dates:
        TransmodelNonOperatingDatesExceptionsRepo(db).bulk_insert(
            operations.non_operating_dates
        )

    if operations.serviced_organisation_vehicle_journeys:
        saved_so_vjs = TransmodelServicedOrganisationVehicleJourneyRepo(db).bulk_insert(
            operations.serviced_organisation_vehicle_journeys
        )

        saved_map = {
            orig.id: saved
            for orig, saved in zip(
                operations.serviced_organisation_vehicle_journeys, saved_so_vjs
            )
        }

        working_days: list[TransmodelServicedOrganisationWorkingDays] = []
        for orig_vj, patterns in operations.working_days_patterns:
            saved_vj = saved_map[orig_vj.id]
            working_days.extend(
                create_serviced_organisation_working_days(saved_vj, patterns)
            )

        if working_days:
            TransmodelServicedOrganisationWorkingDaysRepo(db).bulk_insert(working_days)

    log.info(
        "Processed journey operations",
        journey_id=tm_vj.id,
        profiles=len(operations.operating_profiles),
        op_dates=len(operations.operating_dates),
        non_op_dates=len(operations.non_operating_dates),
        serviced_org_vjs=len(operations.serviced_organisation_vehicle_journeys),
    )
