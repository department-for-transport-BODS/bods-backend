"""
Tables prefixed with naptan_
"""

from typing import Any, Iterable

from common_layer.exceptions.pipeline_exceptions import PipelineException
from sqlalchemy import Select, select
from structlog import get_logger

from ..models.model_naptan import NaptanAdminArea, NaptanLocality, NaptanStopPoint
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepository, BaseRepositoryWithId, SqlDB

logger = get_logger()


class NaptanStopPointRepo(BaseRepository[NaptanStopPoint]):
    """
    Repository for managing StopPoint entities
    """

    def __init__(self, db: SqlDB):
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
    def get_by_atco_code(self, atco_code: str) -> NaptanStopPoint | None:
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

    @handle_repository_errors
    def get_by_locality_ids(self, locality_ids: list[int]) -> list[NaptanStopPoint]:
        """
        Get all stops in a locality
        """
        statement = self._build_query().where(self._model.locality_id.in_(locality_ids))
        return self._fetch_all(statement)

    def get_count(self, atco_codes: list[str], **filter_kwargs) -> int:
        try:
            with self._db.session_scope() as session:
                query = session.query(NaptanStopPoint).filter(
                    NaptanStopPoint.atco_code.in_(atco_codes)
                )
                if filter_kwargs:
                    query = query.filter_by(**filter_kwargs)
                result = query.count()
        except Exception as exc:
            message = f"Exception counting StopPoints with atco_code in {atco_codes} and fields {filter_kwargs}"
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return result

    def get_stop_area_map(self) -> Iterable[dict[str, Any]]:
        """
        Return a map of { <atco_code>: <stop_areas> } for all stops, excluding those with no stop areas.
        """
        try:
            with self._db.session_scope() as session:
                stops = (
                    session.query(
                        NaptanStopPoint.atco_code,
                        NaptanStopPoint.stop_areas,
                    )
                    .filter(NaptanStopPoint.stop_areas != [])
                    .all()
                )
                return {stop.atco_code: stop.stop_areas for stop in stops}
        except Exception as exc:
            message = "Error retrieving stops excluding empty stop areas."
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc


class NaptanLocalityRepo(BaseRepository[NaptanLocality]):
    """Repository for managing Naptan Locality entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, NaptanLocality)

    @handle_repository_errors
    def get_by_id(self, gazetteer_id: str) -> NaptanLocality | None:
        """
        Get by gazetteer_id
        This table does not have an autogenerated id column
        As it's from the NAPTAN Dataset
        """
        statement = self._build_query().where(self._model.gazetteer_id == gazetteer_id)
        return self._fetch_one(statement)


class NaptanAdminAreaRepo(BaseRepositoryWithId[NaptanAdminArea]):
    """Repository for managing Naptan Admin Area entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, NaptanAdminArea)
