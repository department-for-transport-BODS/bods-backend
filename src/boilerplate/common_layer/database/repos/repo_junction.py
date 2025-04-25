"""
Repos for Many to Many Relationhip Tables
AKA: Associative Entity, Junction Tables, Jump Tables
"""

from sqlalchemy import distinct, literal, select
from sqlalchemy.dialects.postgresql import insert

from ..models import (
    OrganisationDatasetRevisionAdminAreas,
    OrganisationDatasetRevisionLocalities,
    TransmodelServicePattern,
    TransmodelServicePatternAdminAreas,
    TransmodelServicePatternLocality,
    TransmodelServiceServicePattern,
    TransmodelTracksVehicleJourney,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepository, SqlDB


class TransmodelServiceServicePatternRepo(
    BaseRepository[TransmodelServiceServicePattern]
):
    """
    Repository for managing Service-ServicePattern associations
    transmodel_service_service_patterns
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelServiceServicePattern)

    @handle_repository_errors
    def get_by_service_id(
        self, service_id: int
    ) -> list[TransmodelServiceServicePattern]:
        """
        Get transmodel_service pattern rows mapped to a row in transmodel_service
        """
        statement = select(self._model).where(self._model.service_id == service_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_service_ids(
        self, service_ids: list[int]
    ) -> list[TransmodelServiceServicePattern]:
        """
        Get transmodel_servicepattern rows mapped to a list of transmodel_service row ids
        """
        statement = select(self._model).where(self._model.service_id.in_(service_ids))
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_pattern_id(
        self, pattern_id: int
    ) -> list[TransmodelServiceServicePattern]:
        """
        Get transmodel_services mapped to a transmodel_servicepattern
        """
        statement = select(self._model).where(
            self._model.servicepattern_id == pattern_id
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_pattern_ids(
        self, pattern_ids: list[int]
    ) -> list[TransmodelServiceServicePattern]:
        """
        Get Services mapped to a list of transmodel_servicepattern row ids
        """
        statement = select(self._model).where(
            self._model.servicepattern_id.in_(pattern_ids)
        )
        return self._fetch_all(statement)


class TransmodelServicePatternLocalityRepo(
    BaseRepository[TransmodelServicePatternLocality]
):
    """
    Repository for managing ServicePattern-Locality associations
    transmodel_servicepattern_localities
    """

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelServicePatternLocality)

    @handle_repository_errors
    def get_by_pattern_id(
        self, pattern_id: int
    ) -> list[TransmodelServicePatternLocality]:
        """Get localities associated with a service pattern"""
        statement = self._build_query().where(
            self._model.servicepattern_id == pattern_id
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_pattern_ids(
        self, pattern_ids: list[int]
    ) -> list[TransmodelServicePatternLocality]:
        """Get localities associated with multiple service patterns"""
        statement = self._build_query().where(
            self._model.servicepattern_id.in_(pattern_ids)
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_locality_id(
        self, locality_id: str
    ) -> list[TransmodelServicePatternLocality]:
        """Get service patterns associated with a locality"""
        statement = self._build_query().where(self._model.locality_id == locality_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_locality_ids(
        self, locality_ids: list[str]
    ) -> list[TransmodelServicePatternLocality]:
        """Get service patterns associated with multiple localities"""
        statement = self._build_query().where(self._model.locality_id.in_(locality_ids))
        return self._fetch_all(statement)


class OrganisationDatasetRevisionLocalitiesRepo(
    BaseRepository[OrganisationDatasetRevisionLocalities]
):
    """
    Repository for managing DatasetRevision-Locality associations
    organisation_datasetrevision_localities
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, OrganisationDatasetRevisionLocalities)

    @handle_repository_errors
    def get_by_datasetrevision_id(
        self, datasetrevision_id: int
    ) -> list[OrganisationDatasetRevisionLocalities]:
        """Get localities associated with a dataset revision"""
        statement = self._build_query().where(
            self._model.datasetrevision_id == datasetrevision_id
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_datasetrevision_ids(
        self, datasetrevision_ids: list[int]
    ) -> list[OrganisationDatasetRevisionLocalities]:
        """Get localities associated with multiple dataset revisions"""
        statement = self._build_query().where(
            self._model.datasetrevision_id.in_(datasetrevision_ids)
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_locality_id(
        self, locality_id: str
    ) -> list[OrganisationDatasetRevisionLocalities]:
        """Get dataset revisions associated with a locality"""
        statement = self._build_query().where(self._model.locality_id == locality_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_locality_ids(
        self, locality_ids: list[str]
    ) -> list[OrganisationDatasetRevisionLocalities]:
        """Get dataset revisions associated with multiple localities"""
        statement = self._build_query().where(self._model.locality_id.in_(locality_ids))
        return self._fetch_all(statement)

    @handle_repository_errors
    def insert_from_revision_id(self, revision_id: int) -> None:
        """
        Bulk insert locality associations
        Presumes that TransmodelServicePatternLocality has been populated
        """
        self._log.debug(
            "Bulk inserting locality associations from service patterns using ORM",
            revision_id=revision_id,
        )

        # 1. Construct a subquery to get all relevant locality IDs
        locality_subquery = (
            select(distinct(TransmodelServicePatternLocality.locality_id))
            .join(
                TransmodelServicePattern,
                TransmodelServicePatternLocality.servicepattern_id
                == TransmodelServicePattern.id,
            )
            .where(TransmodelServicePattern.revision_id == revision_id)
            .subquery()
        )

        # 2. Create the values select statement with proper SQLAlchemy literals
        values_select = select(
            literal(revision_id).label("datasetrevision_id"),
            locality_subquery.c.locality_id.label("locality_id"),
        )

        # 3. Create the insert statement using the from_select method
        insert_stmt = insert(OrganisationDatasetRevisionLocalities).from_select(
            ["datasetrevision_id", "locality_id"],
            values_select,
        )

        # 4. Add the ON CONFLICT DO NOTHING clause
        insert_stmt = insert_stmt.on_conflict_do_nothing(
            index_elements=["datasetrevision_id", "locality_id"]
        )

        with self._db.session_scope() as session:
            session.execute(insert_stmt)

        self._log.debug("Bulk insert of locality associations completed")


class TransmodelServicePatternAdminAreaRepo(
    BaseRepository[TransmodelServicePatternAdminAreas]
):
    """
    Repository for managing ServicePattern-AdminArea associations
    transmodel_servicepattern_admin_areas
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, TransmodelServicePatternAdminAreas)

    @handle_repository_errors
    def get_by_pattern_id(
        self, pattern_id: int
    ) -> list[TransmodelServicePatternAdminAreas]:
        """Get admin areas associated with a service pattern"""
        statement = self._build_query().where(
            self._model.servicepattern_id == pattern_id
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_pattern_ids(
        self, pattern_ids: list[int]
    ) -> list[TransmodelServicePatternAdminAreas]:
        """Get admin areas associated with multiple service patterns"""
        statement = self._build_query().where(
            self._model.servicepattern_id.in_(pattern_ids)
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_admin_area_id(
        self, admin_area_id: int
    ) -> list[TransmodelServicePatternAdminAreas]:
        """Get service patterns associated with an admin area"""
        statement = self._build_query().where(self._model.adminarea_id == admin_area_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_admin_area_ids(
        self, admin_area_ids: list[int]
    ) -> list[TransmodelServicePatternAdminAreas]:
        """Get service patterns associated with multiple admin areas"""
        statement = self._build_query().where(
            self._model.adminarea_id.in_(admin_area_ids)
        )
        return self._fetch_all(statement)


class OrganisationDatasetRevisionAdminAreasRepo(
    BaseRepository[OrganisationDatasetRevisionAdminAreas]
):
    """
    Repository for managing DatasetRevision-AdminArea associations
    organisation_datasetrevision_admin_areas
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, OrganisationDatasetRevisionAdminAreas)

    @handle_repository_errors
    def get_by_datasetrevision_id(
        self, datasetrevision_id: int
    ) -> list[OrganisationDatasetRevisionAdminAreas]:
        """Get admin areas associated with a dataset revision"""
        statement = self._build_query().where(
            self._model.datasetrevision_id == datasetrevision_id
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_datasetrevision_ids(
        self, datasetrevision_ids: list[int]
    ) -> list[OrganisationDatasetRevisionAdminAreas]:
        """Get admin areas associated with multiple dataset revisions"""
        statement = self._build_query().where(
            self._model.datasetrevision_id.in_(datasetrevision_ids)
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_admin_area_id(
        self, admin_area_id: int
    ) -> list[OrganisationDatasetRevisionAdminAreas]:
        """Get dataset revisions associated with an admin area"""
        statement = self._build_query().where(self._model.adminarea_id == admin_area_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_admin_area_ids(
        self, admin_area_ids: list[int]
    ) -> list[OrganisationDatasetRevisionAdminAreas]:
        """Get dataset revisions associated with multiple admin areas"""
        statement = self._build_query().where(
            self._model.adminarea_id.in_(admin_area_ids)
        )
        return self._fetch_all(statement)

    @handle_repository_errors
    def insert_from_revision_id(self, revision_id: int) -> None:
        """
        Bulk insert admin area associations
        Presumes that TransmodelServicePatternAdminAreas has been populated
        """
        self._log.debug(
            "Bulk inserting admin area associations from service patterns using ORM",
            revision_id=revision_id,
        )

        # 1. Construct a subquery to get all relevant admin area IDs
        admin_area_subquery = (
            select(distinct(TransmodelServicePatternAdminAreas.adminarea_id))
            .join(
                TransmodelServicePattern,
                TransmodelServicePatternAdminAreas.servicepattern_id
                == TransmodelServicePattern.id,
            )
            .where(TransmodelServicePattern.revision_id == revision_id)
            .subquery()
        )

        # 2. Create the values select statement with proper SQLAlchemy literals
        values_select = select(
            literal(revision_id).label("datasetrevision_id"),
            admin_area_subquery.c.adminarea_id.label("adminarea_id"),
        )

        # 3. Create the insert statement using the from_select method
        insert_stmt = insert(OrganisationDatasetRevisionAdminAreas).from_select(
            ["datasetrevision_id", "adminarea_id"],
            values_select,
        )

        # 4. Add the ON CONFLICT DO NOTHING clause
        insert_stmt = insert_stmt.on_conflict_do_nothing(
            index_elements=["datasetrevision_id", "adminarea_id"]
        )

        with self._db.session_scope() as session:
            session.execute(insert_stmt)

        self._log.debug("Bulk insert of admin area associations completed")


class TransmodelTracksVehicleJourneyRepo(
    BaseRepository[TransmodelTracksVehicleJourney]
):
    """Repository for managing Tracks Vehicle Journey associations"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelTracksVehicleJourney)

    @handle_repository_errors
    def get_by_vehicle_journey_ids(
        self, vehicle_journey_ids: list[int]
    ) -> list[TransmodelTracksVehicleJourney]:
        """
        Get TransmodelTracksVehicleJourney by Vehicle Journey Ids
        """
        if not vehicle_journey_ids:
            return []
        statement = self._build_query().where(
            self._model.vehicle_journey_id.in_(vehicle_journey_ids)
        )
        return self._fetch_all(statement)
