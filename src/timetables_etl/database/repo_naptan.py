"""
Tables prefixed with naptan_
"""

from typing import Optional

from sqlalchemy import Select, select

from .model_naptan import AdminArea, District, Locality, StopPoint, UILta
from .repo_common import BaseRepository, BodsDB, handle_repository_errors


class StopPointRepository(BaseRepository[StopPoint]):
    """
    Repository for managing StopPoint entities
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, StopPoint)

    def _build_query(self) -> Select:
        """Build base query with common joins"""
        return select(self._model).order_by(self._model.atco_code)

    @handle_repository_errors
    def get_by_atco_code(self, atco_code: str) -> Optional[StopPoint]:
        """
        Get a stop point by its ATCO code
        """
        statement = self._build_query().where(self._model.atco_code == atco_code)
        return self._fetch_one(statement)

    @handle_repository_errors
    def get_by_admin_area(
        self, admin_area_id: int, limit: int | None = None
    ) -> list[StopPoint]:
        """
        Get all stops in an admin area
        """
        statement = self._build_query().where(
            self._model.admin_area_id == admin_area_id
        )
        if limit:
            statement = statement.limit(limit)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_locality(
        self, locality_id: int, limit: int | None = None
    ) -> list[StopPoint]:
        """
        Get all stops in a locality
        """
        statement = self._build_query().where(self._model.locality_id == locality_id)
        if limit:
            statement = statement.limit(limit)
        return self._fetch_all(statement)


class LocalityRepository(BaseRepository[Locality]):
    """
    Repository for managing Locality entities
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, Locality)

    @handle_repository_errors
    def get_by_gazetteer_id(self, gazetteer_id: str) -> Optional[Locality]:
        """
        Get a locality by its gazetteer ID
        """
        statement = self._build_query().where(self._model.gazetteer_id == gazetteer_id)
        return self._fetch_one(statement)

    @handle_repository_errors
    def get_by_admin_area(
        self, admin_area_id: int, limit: int | None = None
    ) -> list[Locality]:
        """
        Get all localities in an admin area
        """
        statement = self._build_query().where(
            self._model.admin_area_id == admin_area_id
        )
        if limit:
            statement = statement.limit(limit)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_district(
        self, district_id: int, limit: int | None = None
    ) -> list[Locality]:
        """
        Get all localities in a district
        """
        statement = self._build_query().where(self._model.district_id == district_id)
        if limit:
            statement = statement.limit(limit)
        return self._fetch_all(statement)

    def _build_query(self) -> Select:
        """Build base query with common joins and ordering"""
        return select(self._model).order_by(self._model.name)


class DistrictRepository(BaseRepository[District]):
    """
    Repository for managing District entities
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, District)

    def _build_query(self) -> Select:
        """Build base query with ordering"""
        return select(self._model).order_by(self._model.name)

    @handle_repository_errors
    def get_by_name(self, name: str) -> District | None:
        """
        Get a district by its exact name
        """
        statement = self._build_query().where(self._model.name == name)
        return self._fetch_one(statement)


class UILtaRepository(BaseRepository[UILta]):
    """
    Repository for managing UILta entities
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, UILta)

    @handle_repository_errors
    def get_by_name(self, name: str) -> UILta | None:
        """
        Get a UI LTA by its exact name
        """
        statement = self._build_query().where(self._model.name == name)
        return self._fetch_one(statement)


class AdminAreaRepository(BaseRepository[AdminArea]):
    """
    Repository for managing AdminArea entities
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, AdminArea)

    def _build_query(self) -> Select:
        """Build base query with ordering"""
        return select(self._model).order_by(self._model.name)

    @handle_repository_errors
    def get_by_atco_code(self, atco_code: str) -> AdminArea | None:
        """
        Get an admin area by its ATCO code
        """
        statement = self._build_query().where(self._model.atco_code == atco_code)
        return self._fetch_one(statement)

    @handle_repository_errors
    def get_by_ui_lta(self, ui_lta_id: int) -> list[AdminArea]:
        """
        Get all admin areas for a specific UI LTA
        """
        statement = self._build_query().where(self._model.ui_lta_id == ui_lta_id)
        return self._fetch_all(statement)

    @handle_repository_errors
    def get_by_traveline_region(self, region_id: str) -> list[AdminArea]:
        """
        Get all admin areas in a traveline region
        """
        statement = self._build_query().where(
            self._model.traveline_region_id == region_id
        )
        return self._fetch_all(statement)
