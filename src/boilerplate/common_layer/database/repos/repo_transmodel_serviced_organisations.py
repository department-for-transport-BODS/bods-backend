"""
Transmodel Serviced Organisation Related Repos
"""

from sqlalchemy import ColumnElement, Select, and_, or_

from ..client import SqlDB
from ..models.model_transmodel_serviced_organisations import (
    TransmodelServicedOrganisations,
    TransmodelServicedOrganisationVehicleJourney,
    TransmodelServicedOrganisationWorkingDays,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepositoryWithId


class TransmodelServicedOrganisationsRepo(
    BaseRepositoryWithId[TransmodelServicedOrganisations]
):
    """Repository for managing Transmodel Serviced Organisations entities"""

    def __init__(self, db: SqlDB):
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
    BaseRepositoryWithId[TransmodelServicedOrganisationWorkingDays]
):
    """Repository for managing Serviced Organisation Working Days entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelServicedOrganisationWorkingDays)

    def get_by_serviced_organisation_vehicle_journey_id(
        self, serviced_organisation_vehicle_journey_ids: list[int]
    ) -> list[TransmodelServicedOrganisationWorkingDays]:
        """
        Get serviced organisation working days by
        serviced_organisation_vehicle_journey_id(s).
        """
        if not serviced_organisation_vehicle_journey_ids:
            return []
        statement = self._build_query().where(
            self._model.serviced_organisation_vehicle_journey_id.in_(
                serviced_organisation_vehicle_journey_ids
            )
        )
        return self._fetch_all(statement)


class TransmodelServicedOrganisationVehicleJourneyRepo(
    BaseRepositoryWithId[TransmodelServicedOrganisationVehicleJourney]
):
    """Repository for managing Serviced Organisation Vehicle Journey entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelServicedOrganisationVehicleJourney)

    def get_by_vehicle_journey_ids(
        self, vehicle_journey_ids: list[int]
    ) -> list[TransmodelServicedOrganisationVehicleJourney]:
        """
        Get serviced organisation vehicle journey by vehicle_journey_id
        """
        if not vehicle_journey_ids:
            return []
        statement = self._build_query().where(
            self._model.vehicle_journey_id.in_(vehicle_journey_ids)
        )
        return self._fetch_all(statement)
