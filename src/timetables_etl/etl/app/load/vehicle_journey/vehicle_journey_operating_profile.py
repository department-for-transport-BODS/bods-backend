"""
transmodel_vehiclejourny Operating profiles generation
"""

from common_layer.database.models import (
    TransmodelServicedOrganisationWorkingDays,
    TransmodelVehicleJourney,
)
from common_layer.database.repos import (
    TransmodelNonOperatingDatesExceptionsRepo,
    TransmodelOperatingDatesExceptionsRepo,
    TransmodelOperatingProfileRepo,
    TransmodelServicedOrganisationVehicleJourneyRepo,
    TransmodelServicedOrganisationWorkingDaysRepo,
)
from common_layer.xml.txc.models import TXCVehicleJourney
from structlog.stdlib import get_logger

from ...transform.vehicle_journey_operations import (
    create_serviced_organisation_working_days,
    create_vehicle_journey_operations,
)
from ..models_context import OperatingProfileProcessingContext

log = get_logger()


def process_operating_profile(
    tm_vj: TransmodelVehicleJourney,
    txc_vj: TXCVehicleJourney,
    context: OperatingProfileProcessingContext,
):
    """
    Process a single Operating Profile
    """
    operations = create_vehicle_journey_operations(
        txc_vj=txc_vj,
        tm_vj=tm_vj,
        context=context,
    )

    if operations.operating_profiles:
        TransmodelOperatingProfileRepo(context.db).bulk_insert(
            operations.operating_profiles
        )

    if operations.operating_dates:
        TransmodelOperatingDatesExceptionsRepo(context.db).bulk_insert(
            operations.operating_dates
        )

    if operations.non_operating_dates:
        TransmodelNonOperatingDatesExceptionsRepo(context.db).bulk_insert(
            operations.non_operating_dates
        )

    if operations.serviced_organisation_vehicle_journeys:
        saved_so_vjs = TransmodelServicedOrganisationVehicleJourneyRepo(
            context.db
        ).bulk_insert(operations.serviced_organisation_vehicle_journeys)

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
            TransmodelServicedOrganisationWorkingDaysRepo(context.db).bulk_insert(
                working_days
            )

    log.info(
        "Processed journey operations",
        journey_id=tm_vj.id,
        profiles=len(operations.operating_profiles),
        op_dates=len(operations.operating_dates),
        non_op_dates=len(operations.non_operating_dates),
        serviced_org_vjs=len(operations.serviced_organisation_vehicle_journeys),
    )
