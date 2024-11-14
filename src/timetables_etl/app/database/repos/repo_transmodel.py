"""
Transmodel table repos
"""

from ..client import BodsDB
from ..models import (
    TransmodelBookingArrangements,
    TransmodelFlexibleServiceOperationPeriod,
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
    TransmodelOperatingProfile,
    TransmodelService,
    TransmodelServicedOrganisations,
    TransmodelServicedOrganisationVehicleJourney,
    TransmodelServicedOrganisationWorkingDays,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelVehicleJourney,
)
from .repo_common import BaseRepository, handle_repository_errors


class TransmodelServiceRepo(BaseRepository[TransmodelService]):
    """
    Repository for managing Transmodel Service entities
    Table: transmodel_service
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelService)

    @handle_repository_errors
    def get_by_id(self, service_id: int) -> TransmodelService | None:
        """
        Get by ID
        """
        statement = self._build_query().where(self._model.id == service_id)
        return self._fetch_one(statement)


class TransmodelVehicleJourneyRepo(BaseRepository[TransmodelVehicleJourney]):
    """
    Repository for managing Transmodel Vehicle Journey entities
    Table: transmodel_vehiclejourney
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelVehicleJourney)

    @handle_repository_errors
    def get_by_id(self, journey_id: int) -> TransmodelVehicleJourney | None:
        """
        Get by ID
        """
        statement = self._build_query().where(self._model.id == journey_id)
        return self._fetch_one(statement)


class TransmodelServicePatternRepo(BaseRepository[TransmodelServicePattern]):
    """
    Repository for managing Transmodel Service Pattern entities
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelServicePattern)

    @handle_repository_errors
    def get_by_id(self, pattern_id: int) -> TransmodelServicePattern | None:
        """
        Get by ID
        """
        statement = self._build_query().where(self._model.id == pattern_id)
        return self._fetch_one(statement)


class TransmodelServicedOrganisationsRepo(
    BaseRepository[TransmodelServicedOrganisations]
):
    """Repository for managing Transmodel Serviced Organisations entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelServicedOrganisations)

    @handle_repository_errors
    def get_by_id(self, org_id: int) -> TransmodelServicedOrganisations | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == org_id)
        return self._fetch_one(statement)


class TransmodelFlexibleServiceOperationPeriodRepo(
    BaseRepository[TransmodelFlexibleServiceOperationPeriod]
):
    """Repository for managing Flexible Service Operation Period entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelFlexibleServiceOperationPeriod)

    @handle_repository_errors
    def get_by_id(
        self, period_id: int
    ) -> TransmodelFlexibleServiceOperationPeriod | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == period_id)
        return self._fetch_one(statement)


class TransmodelOperatingProfileRepo(BaseRepository[TransmodelOperatingProfile]):
    """Repository for managing Operating Profile entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelOperatingProfile)

    @handle_repository_errors
    def get_by_id(self, profile_id: int) -> TransmodelOperatingProfile | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == profile_id)
        return self._fetch_one(statement)


class TransmodelOperatingDatesExceptionsRepo(
    BaseRepository[TransmodelOperatingDatesExceptions]
):
    """Repository for managing Operating Dates Exceptions entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelOperatingDatesExceptions)

    @handle_repository_errors
    def get_by_id(self, exception_id: int) -> TransmodelOperatingDatesExceptions | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == exception_id)
        return self._fetch_one(statement)


class TransmodelNonOperatingDatesExceptionsRepo(
    BaseRepository[TransmodelNonOperatingDatesExceptions]
):
    """Repository for managing Non Operating Dates Exceptions entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelNonOperatingDatesExceptions)

    @handle_repository_errors
    def get_by_id(
        self, exception_id: int
    ) -> TransmodelNonOperatingDatesExceptions | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == exception_id)
        return self._fetch_one(statement)


class TransmodelServicedOrganisationVehicleJourneyRepo(
    BaseRepository[TransmodelServicedOrganisationVehicleJourney]
):
    """Repository for managing Serviced Organisation Vehicle Journey entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelServicedOrganisationVehicleJourney)

    @handle_repository_errors
    def get_by_id(
        self, relation_id: int
    ) -> TransmodelServicedOrganisationVehicleJourney | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == relation_id)
        return self._fetch_one(statement)


class TransmodelServicedOrganisationWorkingDaysRepo(
    BaseRepository[TransmodelServicedOrganisationWorkingDays]
):
    """Repository for managing Serviced Organisation Working Days entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelServicedOrganisationWorkingDays)

    @handle_repository_errors
    def get_by_id(
        self, working_days_id: int
    ) -> TransmodelServicedOrganisationWorkingDays | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == working_days_id)
        return self._fetch_one(statement)


class TransmodelServicePatternStopRepo(BaseRepository[TransmodelServicePatternStop]):
    """Repository for managing Service Pattern Stop entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelServicePatternStop)

    @handle_repository_errors
    def get_by_id(self, stop_id: int) -> TransmodelServicePatternStop | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == stop_id)
        return self._fetch_one(statement)


class TransmodelBookingArrangementsRepo(BaseRepository[TransmodelBookingArrangements]):
    """Repository for managing Booking Arrangements entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelBookingArrangements)

    @handle_repository_errors
    def get_by_id(self, arrangement_id: int) -> TransmodelBookingArrangements | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == arrangement_id)
        return self._fetch_one(statement)
