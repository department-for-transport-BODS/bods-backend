"""
Tables prefixed with naptan_
"""

from typing import AsyncIterator, Iterator

from common_layer.exceptions.pipeline_exceptions import PipelineException
from sqlalchemy import select
from structlog import get_logger

from ..models.model_naptan import NaptanAdminArea, NaptanLocality, NaptanStopPoint
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepository, BaseRepositoryWithId, SqlDB

logger = get_logger()


class NaptanStopPointRepo(BaseRepository[NaptanStopPoint]):
    """
    Repository for managing StopPoint entities
    """

    def __init__(self, db: SqlDB) -> None:
        super().__init__(db, NaptanStopPoint)

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

    def get_ids_by_atco(self, atco_codes: list[str]) -> dict[str, int]:
        """
        Get the IDs (PKs) of NaPTAN stop points given a list of AtcoCodes.

        Returns dict[str, int] mapping AtcoCode -> ID in the database.
        """
        if not atco_codes:
            return {}
        statement = select(self._model.atco_code, self._model.id).where(
            self._model.atco_code.in_(atco_codes)
        )
        with self._db.session_scope() as session:
            results = list(session.execute(statement).all())
            return {row[0]: row[1] for row in results}

    def stream_naptan_ids(self, batch_size: int = 1000) -> Iterator[dict[str, int]]:
        """Fetch NaPTAN stop point IDs in batches."""
        offset = 0
        while True:
            with self._db.session_scope() as session:
                results = session.execute(
                    select(self._model.atco_code, self._model.id)
                    .order_by(self._model.atco_code)
                    .offset(offset)
                    .limit(batch_size)
                ).all()

                if not results:
                    break  # No more data

                yield {row[0]: row[1] for row in results}
                offset += batch_size

    @handle_repository_errors
    def get_by_naptan_codes(
        self, naptan_codes: list[str]
    ) -> tuple[list[NaptanStopPoint], list[str]]:
        """
        Get stop points by their NaPTAN codes
        Returns tuple of (found_stops, missing_naptan_codes)
        """
        statement = self._build_query().where(self._model.naptan_code.in_(naptan_codes))
        found_stops = self._fetch_all(statement)

        found_naptan_codes = {stop.naptan_code for stop in found_stops}
        missing_naptan_codes = [
            code for code in naptan_codes if code not in found_naptan_codes
        ]

        return found_stops, missing_naptan_codes

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

    def get_count(
        self, atco_codes: list[str], **filter_kwargs: str | bool | int | None
    ) -> int:
        """
        Get number of Stop Points in the DB by atco_code
        """
        try:
            with self._db.session_scope() as session:
                query = session.query(NaptanStopPoint).filter(
                    NaptanStopPoint.atco_code.in_(atco_codes)
                )
                if filter_kwargs:
                    query = query.filter_by(**filter_kwargs)
                result = query.count()
        except Exception as exc:
            message = (
                f"Exception counting StopPoints with atco_code in {atco_codes} "
                f"and fields {filter_kwargs}"
            )
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc

        return result


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
