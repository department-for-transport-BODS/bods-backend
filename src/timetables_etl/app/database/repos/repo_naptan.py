"""
Tables prefixed with naptan_
"""

from typing import Optional

from sqlalchemy import Select, select

from ..models.model_naptan import NaptanAdminArea, NaptanLocality, NaptanStopPoint
from .repo_common import BaseRepository, BodsDB, handle_repository_errors


class NaptanStopPointRepo(BaseRepository[NaptanStopPoint]):
    """
    Repository for managing StopPoint entities
    """

    def __init__(self, db: BodsDB):
        super().__init__(db, NaptanStopPoint)

    def _build_query(self) -> Select:
        """Build base query with common joins"""
        return select(self._model).order_by(self._model.atco_code)

    @handle_repository_errors
    def get_by_id(self, table_id: str) -> NaptanStopPoint | None:
        """Get by"""
        statement = self._build_query().where(self._model.id == table_id)
        return self._fetch_one(statement)

    @handle_repository_errors
    def get_by_atco_code(self, atco_code: str) -> Optional[NaptanStopPoint]:
        """
        Get a stop point by its ATCO code
        """
        statement = self._build_query().where(self._model.atco_code == atco_code)
        return self._fetch_one(statement)

    @handle_repository_errors
    def get_by_atco_codes(
        self, atco_codes: list[str]
    ) -> tuple[list[NaptanStopPoint], list[str]]:
        """
        Get stop points by their ATCO codes
        Returns tuple of (found_stops, missing_atco_codes)
        """
        statement = self._build_query().where(self._model.atco_code.in_(atco_codes))
        found_stops = self._fetch_all(statement)

        found_atco_codes = {stop.atco_code for stop in found_stops}
        missing_atco_codes = [
            code for code in atco_codes if code not in found_atco_codes
        ]

        return found_stops, missing_atco_codes

    @handle_repository_errors
    def get_by_admin_area(
        self, admin_area_id: int, limit: int | None = None
    ) -> list[NaptanStopPoint]:
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
    ) -> list[NaptanStopPoint]:
        """
        Get all stops in a locality
        """
        statement = self._build_query().where(self._model.locality_id == locality_id)
        if limit:
            statement = statement.limit(limit)
        return self._fetch_all(statement)


class NaptanLocalityRepo(BaseRepository[NaptanLocality]):
    """Repository for managing Naptan Locality entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, NaptanLocality)

    @handle_repository_errors
    def get_by_id(self, gazetteer_id: str) -> NaptanLocality | None:
        """Get by gazetteer_id"""
        statement = self._build_query().where(self._model.gazetteer_id == gazetteer_id)
        return self._fetch_one(statement)


class NaptanAdminAreaRepo(BaseRepository[NaptanAdminArea]):
    """Repository for managing Naptan Admin Area entities"""

    def __init__(self, db: BodsDB):
        super().__init__(db, NaptanAdminArea)

    @handle_repository_errors
    def get_by_id(self, area_id: int) -> NaptanAdminArea | None:
        """Get by ID"""
        statement = self._build_query().where(self._model.id == area_id)
        return self._fetch_one(statement)
