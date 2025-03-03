"""
Transmodel table repos
"""

from collections import defaultdict
from datetime import date
from typing import Literal

from sqlalchemy import tuple_

from ..client import SqlDB
from ..models import (
    TransmodelBankHolidays,
    TransmodelService,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelStopActivity,
    TransmodelTracks,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepository, BaseRepositoryWithId


class TransmodelServiceRepo(BaseRepositoryWithId[TransmodelService]):
    """
    Repository for managing Transmodel Service entities
    Table: transmodel_service
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelService)

    @handle_repository_errors
    def get_by_revision_id(self, revision_id: int) -> list[TransmodelService]:
        """
        Get multiple TransmodelService by OrganisationDatasetRevision ID
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_txcfileattributes_ids(
        self, txcfileattributes_ids: list[int]
    ) -> list[TransmodelService]:
        """
        Get multiple TransmodelService by a list of TXCFileAttributes Ids
        """
        if not txcfileattributes_ids:
            return []
        statement = self._build_query().where(
            self._model.txcfileattributes_id.in_(txcfileattributes_ids)
        )
        return self._fetch_all(statement)


class TransmodelServicePatternRepo(BaseRepositoryWithId[TransmodelServicePattern]):
    """
    Repository for managing Transmodel Service Pattern entities
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelServicePattern)

    @handle_repository_errors
    def get_by_revision_id(self, revision_id: int) -> list[TransmodelServicePattern]:
        """
        Get a list of TransmodelServicePattern by OrganisationDatasetRevision ID
        """
        statement = self._build_query().where(self._model.revision_id == revision_id)
        return self._fetch_all(statement)


class TransmodelServicePatternStopRepo(
    BaseRepositoryWithId[TransmodelServicePatternStop]
):
    """Repository for managing Service Pattern Stop entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelServicePatternStop)

    @handle_repository_errors
    def get_by_service_pattern_ids(
        self, pattern_ids: list[int]
    ) -> list[TransmodelServicePatternStop]:
        """
        Get a list of TransmodelServicePatternStop by TransmodelServicePattern
        """
        statement = self._build_query().where(
            self._model.service_pattern_id.in_(pattern_ids)
        )
        return self._fetch_all(statement)


class TransmodelStopActivityRepo(BaseRepositoryWithId[TransmodelStopActivity]):
    """
    Repository for managing TransmodelStopActivity Stop usages
    e.g. pickup, setDown
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelStopActivity)

    @handle_repository_errors
    def get_by_name(self, name: str) -> TransmodelStopActivity | None:
        """Get activity by name"""
        statement = self._build_query().where(self._model.name == name)
        return self._fetch_one(statement)

    @handle_repository_errors
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

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelBankHolidays)

    @handle_repository_errors
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

    @handle_repository_errors
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


class TransmodelTrackRepo(BaseRepositoryWithId[TransmodelTracks]):
    """Repository for managing Track entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelTracks)

    @handle_repository_errors
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
