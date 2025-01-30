"""
Transmodel Data fetching
"""

from common_layer.database.models import (
    TransmodelBookingArrangements,
    TransmodelFlexibleServiceOperationPeriod,
    TransmodelService,
    TransmodelServicedOrganisations,
    TransmodelServicedOrganisationVehicleJourney,
    TransmodelServicedOrganisationWorkingDays,
    TransmodelServicePattern,
    TransmodelServicePatternAdminAreas,
    TransmodelServicePatternLocality,
    TransmodelServicePatternStop,
    TransmodelServiceServicePattern,
    TransmodelStopActivity,
)
from common_layer.database.models.model_transmodel_vehicle_journey import (
    TransmodelVehicleJourney,
)
from common_layer.database.repos import (
    TransmodelBookingArrangementsRepo,
    TransmodelFlexibleServiceOperationPeriodRepo,
    TransmodelServicedOrganisationsRepo,
    TransmodelServicedOrganisationVehicleJourneyRepo,
    TransmodelServicedOrganisationWorkingDaysRepo,
    TransmodelServicePatternAdminAreaRepo,
    TransmodelServicePatternLocalityRepo,
    TransmodelServicePatternRepo,
    TransmodelServicePatternStopRepo,
    TransmodelServiceRepo,
    TransmodelServiceServicePatternRepo,
    TransmodelStopActivityRepo,
    TransmodelVehicleJourneyRepo,
)
from structlog.stdlib import get_logger

from .utils import SqlDB, csv_extractor

logger = get_logger()


@csv_extractor()
def extract_services_by_revision_id(
    db: SqlDB, revision_id: int
) -> list[TransmodelService]:
    """
    Get the list of services associated to a revision_id
    And output to csv
    """
    repo = TransmodelServiceRepo(db)
    return repo.get_by_revision_id(revision_id)


@csv_extractor()
def extract_service_by_id(
    db: SqlDB,
    service_id: int,
) -> TransmodelService | None:
    """
    Extract service details from DB.
    """
    repo = TransmodelServiceRepo(db)
    return repo.get_by_id(service_id)


@csv_extractor()
def extract_servicepatterns_by_ids(
    db: SqlDB, service_pattern_ids: list[int]
) -> list[TransmodelServicePattern]:
    """
    Extract service pattern details from DB.
    """
    repo = TransmodelServicePatternRepo(db)
    return repo.get_by_ids(service_pattern_ids)


@csv_extractor()
def extract_servicepatterns_by_revision_id(
    db: SqlDB, revision_id: int
) -> list[TransmodelServicePattern]:
    """
    Extract service pattern details from DB.
    """
    repo = TransmodelServicePatternRepo(db)
    return repo.get_by_revision_id(revision_id)


@csv_extractor()
def extract_servicepatternstop(
    db: SqlDB, service_pattern_ids: list[int]
) -> list[TransmodelServicePatternStop]:
    """
    Extract the Service Pattern Stops by id
    """
    repo = TransmodelServicePatternStopRepo(db)
    return repo.get_by_service_pattern_ids(service_pattern_ids)


@csv_extractor()
def extract_stopactivity(
    db: SqlDB, stop_activity_ids: list[int]
) -> list[TransmodelStopActivity]:
    """
    Extract stop activity details from DB.
    """
    repo = TransmodelStopActivityRepo(db)
    return repo.get_by_ids(list(set(stop_activity_ids)))


@csv_extractor()
def extract_service_service_patterns(
    db: SqlDB, service_ids: list[int]
) -> list[TransmodelServiceServicePattern]:
    """
    Extract service service patterns details from DB.
    """
    repo = TransmodelServiceServicePatternRepo(db)
    return repo.get_by_service_ids(service_ids)


@csv_extractor()
def extract_servicepattern_localities(
    db: SqlDB, servicepattern_ids: list[int]
) -> list[TransmodelServicePatternLocality]:
    """
    Extract service pattern localities
    """
    repo = TransmodelServicePatternLocalityRepo(db)
    return repo.get_by_pattern_ids(servicepattern_ids)


@csv_extractor()
def extract_servicepattern_admin_areas(
    db: SqlDB, servicepattern_ids: list[int]
) -> list[TransmodelServicePatternAdminAreas]:
    """
    Extract service pattern admin areas from DB.
    """
    repo = TransmodelServicePatternAdminAreaRepo(db)
    return repo.get_by_pattern_ids(servicepattern_ids)


@csv_extractor()
def extract_vehiclejourney(
    db: SqlDB, vehicle_journey_ids: list[int]
) -> list[TransmodelVehicleJourney]:
    """
    Extract vehicle journey details from DB.
    """
    repo = TransmodelVehicleJourneyRepo(db)
    return repo.get_by_ids(vehicle_journey_ids)


@csv_extractor()
def extract_bookingarrangements(
    db: SqlDB, service_ids: list[int]
) -> list[TransmodelBookingArrangements]:
    """
    Extract booking arragements details from DB.
    """
    repo = TransmodelBookingArrangementsRepo(db)
    return repo.get_by_service_ids(service_ids)


@csv_extractor()
def extract_flexibleserviceoperationperiod(
    db: SqlDB, vehicle_journey_ids: list[int]
) -> list[TransmodelFlexibleServiceOperationPeriod]:
    """
    Flexible Service Operation Period
    """
    repo = TransmodelFlexibleServiceOperationPeriodRepo(db)
    return repo.get_by_vehicle_journey_ids(vehicle_journey_ids)


@csv_extractor()
def extract_servicedorganisationvehiclejourney(
    db: SqlDB, vehicle_journey_id: list[int]
) -> list[TransmodelServicedOrganisationVehicleJourney]:
    """
    Extract serviced organisation vehicle journey details from DB.
    """
    repo = TransmodelServicedOrganisationVehicleJourneyRepo(db)
    return repo.get_by_vehicle_journey_ids(vehicle_journey_id)


@csv_extractor()
def extract_servicedorganisations(
    db: SqlDB, serviced_organisation_id: list[int]
) -> list[TransmodelServicedOrganisations]:
    """
    Extract serviced organisation details from DB.
    """
    repo = TransmodelServicedOrganisationsRepo(db)
    return repo.get_by_ids(serviced_organisation_id)


@csv_extractor()
def extract_servicedorganisationworkingdays(
    db: SqlDB, serviced_organisation_vehicle_journey_ids: list[int]
) -> list[TransmodelServicedOrganisationWorkingDays]:
    """
    Extract serviced organisation working days daetails from DB.
    """
    repo = TransmodelServicedOrganisationWorkingDaysRepo(db)
    return repo.get_by_serviced_organisation_vehicle_journey_id(
        serviced_organisation_vehicle_journey_ids
    )
