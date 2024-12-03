"""
Transmodel table repos
"""

from collections import defaultdict
from datetime import date
from typing import Literal

from sqlalchemy import tuple_

from ..client import BodsDB
from ..models import (
    TransmodelBankHolidays,
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
    TransmodelOperatingProfile,
    TransmodelService,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelStopActivity,
    TransmodelTracks,
    TransmodelVehicleJourney,
)
from ..models.model_transmodel_flexible import (
    TransmodelBookingArrangements,
    TransmodelFlexibleServiceOperationPeriod,
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


class TransmodelStopActivityRepo(BaseRepository[TransmodelStopActivity]):
    """
    Repository for managing TransmodelStopActivity Stop usages
    e.g. pickup, setDown
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelStopActivity)

    def get_by_name(self, name: str) -> TransmodelStopActivity | None:
        """Get activity by name"""
        statement = self._build_query().where(self._model.name == name)
        return self._fetch_one(statement)

    def get_activity_map(self) -> dict[str, TransmodelStopActivity]:
        """
        Get mapping of activity name to TransmodelStopActivity model
        The ID ordering can't be guaranteed so needs to be fetched as a reference
        """

        activities = self.get_all()
        return {activity.name: activity for activity in activities}


class TransmodelBankHolidaysRepo(BaseRepository[TransmodelBankHolidays]):
    """
    Repository for getting Bank Holiday Information
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelBankHolidays)

    def get_bank_holidays_in_range(
        self,
        start_date: date,
        end_date: date | None = None,
        divisions: list[Literal["england-and-wales", "scotland"]] | None = None,
    ) -> list[TransmodelBankHolidays]:
        """
        Get bank holidays from a start date, with optional end date
        """
        statement = self._build_query()

        statement = statement.filter(self._model.date >= start_date)
        if end_date is not None:
            statement = statement.filter(self._model.date <= end_date)

        if divisions:
            statement = statement.filter(self._model.division.in_(divisions))

        statement = statement.order_by(self._model.date)

        return self._fetch_all(statement)

    def get_bank_holidays_lookup(
        self,
        start_date: date,
        end_date: date | None = None,
        divisions: list[Literal["england-and-wales", "scotland"]] | None = None,
    ) -> dict[str, list[date]]:
        """
        Get bank holidays organized by txc_element
        """
        holidays = self.get_bank_holidays_in_range(
            start_date=start_date,
            end_date=end_date,
            divisions=divisions,
        )

        holiday_lookup: dict[str, list[date]] = defaultdict(list)
        for holiday in holidays:
            holiday_lookup[holiday.txc_element].append(holiday.date)

        return dict(holiday_lookup)


class TransmodelTrackRepo(BaseRepository[TransmodelTracks]):
    """Repository for managing Track entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelTracks)

    def get_by_stop_pairs(
        self, stop_pairs: list[tuple[str, str]]
    ) -> list[TransmodelTracks]:
        """Get existing tracks by from/to stop pairs"""
        if not stop_pairs:
            return []

        statement = self._build_query().where(
            tuple_(self._model.from_atco_code, self._model.to_atco_code).in_(stop_pairs)
        )
        return self._fetch_all(statement)
