"""
Transmodel Serviced Organisation Related Repos
"""

from sqlalchemy import ColumnElement, Select, and_, or_

from ..client import BodsDB
from ..models.model_transmodel_serviced_organisations import (
    TransmodelServicedOrganisations,
    TransmodelServicedOrganisationVehicleJourney,
    TransmodelServicedOrganisationWorkingDays,
)
from .repo_common import BaseRepository, BaseRepositoryWithId, handle_repository_errors


class TransmodelServicedOrganisationsRepo(
    BaseRepositoryWithId[TransmodelServicedOrganisations]
):
    """Repository for managing Transmodel Serviced Organisations entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, TransmodelServicedOrganisations)

    @handle_repository_errors
    def get_existing_by_name_and_code(
        self, orgs: list[tuple[str | None, str]]
    ) -> list[TransmodelServicedOrganisations]:
        """
        Get existing organizations that match the name and code combinations
        To ensure we are only inserting unique Serviced Organisations
        """
        if not orgs:
            return []

        conditions: list[ColumnElement[bool]] = [
            and_(self._model.name == name, self._model.organisation_code == code)
            for name, code in orgs
        ]

        statement: Select[tuple[TransmodelServicedOrganisations]] = (
            self._build_query().where(or_(*conditions))
        )
        return self._fetch_all(statement)


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
