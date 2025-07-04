"""
Transmodel table repos
"""

from collections import defaultdict
from datetime import date
from typing import Iterator, Literal

from psycopg2.extensions import connection as PsycopgConnection
from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from structlog.stdlib import get_logger

from ..client import SqlDB
from ..dataclasses import ServiceStats
from ..models import (
    TransmodelBankHolidays,
    TransmodelService,
    TransmodelServicePattern,
    TransmodelServicePatternDistance,
    TransmodelServicePatternStop,
    TransmodelStopActivity,
    TransmodelTracks,
)
from .operation_decorator import handle_repository_errors
from .repo_common import BaseRepository, BaseRepositoryWithId

log = get_logger()


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

    def get_service_stats_by_revision_id(self, revision_id: int) -> ServiceStats:
        """
        Get ServiceStats for the given revision id:
        - first_service_start
        - first_expiring_service
        - last_expiring_service
        """
        stmt = select(
            func.min(self._model.start_date),
            func.min(self._model.end_date),
            func.max(self._model.end_date),
        ).where(self._model.revision_id == revision_id)

        with self._db.session_scope() as session:
            result = session.execute(stmt).one_or_none()
            if result is None:
                return ServiceStats(
                    first_service_start=None,
                    first_expiring_service=None,
                    last_expiring_service=None,
                )
            min_start, min_end, max_end = result
            return ServiceStats(
                first_service_start=min_start,
                first_expiring_service=min_end,
                last_expiring_service=max_end,
            )


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
    def get_activity_id_map(self) -> dict[str, int]:
        """
        Get mapping of activity name to TransmodelStopActivity model
        The ID ordering can't be guaranteed so needs to be fetched as a reference
        """

        activities = self.get_all()
        return {activity.name: activity.id for activity in activities}


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

    @handle_repository_errors
    def bulk_insert_ignore_duplicates(
        self, records: list[TransmodelTracks]
    ) -> dict[tuple[str, str], int]:
        """
        Insert multiple records using PostgreSQL's ON CONFLICT DO NOTHING syntax.
        Returns count of records inserted
        """
        if not records:
            return {}

        with self._db.session_scope() as session:
            insert_stmt = insert(self._model).returning(
                self._model.id, self._model.from_atco_code, self._model.to_atco_code
            )
            records_to_create = [record.__dict__ for record in records]
            results = session.execute(insert_stmt, records_to_create)
            tracks = {(row[1], row[2]): row[0] for row in results.fetchall()}
            return tracks

    def stream_distinct_stop_points_with_multiple_rows(
        self, batch_size: int = 10000
    ) -> Iterator[list[tuple[str, str]]]:
        """
        Stream batches of distinct stop point pairs (from_atco_code, to_atco_code)
        that occur more than once.
        """
        raw_conn: PsycopgConnection = self._db.engine.raw_connection()  # type: ignore[assignment]
        try:
            with raw_conn.cursor() as cursor:
                cursor.itersize = batch_size
                query = """
                    SELECT from_atco_code, to_atco_code
                    FROM transmodel_tracks
                    GROUP BY from_atco_code, to_atco_code
                    HAVING COUNT(*) > 1
                    ORDER BY from_atco_code, to_atco_code
                """
                cursor.execute(query)
                batch: list[tuple[str, str]] = []
                for from_code, to_code in cursor:
                    batch.append((from_code, to_code))
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                if batch:
                    yield batch
        finally:
            raw_conn.close()

    def stream_similar_track_pairs_by_stop_points(
        self, stop_point_pairs: list[tuple[str, str]], threshold: float = 20.0
    ) -> Iterator[tuple[tuple[str, str], list[tuple[int, int]]]]:
        """
        Stream similar pairs of (track_a, track_b) grouped by (from_atco_code, to_atco_code)
        where similarity is calculated by Hausdorff Distance within the given threshold in meters
        """
        raw_conn: PsycopgConnection = self._db.engine.raw_connection()  # type: ignore[assignment]
        try:
            with raw_conn.cursor() as cursor:
                cursor.itersize = 10000
                log.info("Fetching similar tracks")
                table_name = self._model.__tablename__

                # Prepare a VALUES list for the stop point pairs
                stop_point_values = ",".join(
                    cursor.mogrify("(%s, %s)", pair).decode("utf-8")
                    for pair in stop_point_pairs
                )

                query = f"""
                    WITH stop_pairs(from_code, to_code) AS (
                        VALUES {stop_point_values}
                    )
                    SELECT
                        a.from_atco_code,
                        a.to_atco_code,
                        json_agg(
                            json_build_object('track_a', a.id, 'track_b', b.id)
                        ) AS similar_pairs
                    FROM {table_name} a
                    JOIN {table_name} b
                        ON a.from_atco_code = b.from_atco_code
                        AND a.to_atco_code = b.to_atco_code
                        AND a.id < b.id
                    JOIN stop_pairs sp
                        ON a.from_atco_code = sp.from_code AND a.to_atco_code = sp.to_code
                    WHERE ST_HausdorffDistance(
                        ST_Transform(a.geometry, 27700),
                        ST_Transform(b.geometry, 27700)
                    ) < %s
                    GROUP BY a.from_atco_code, a.to_atco_code
                    ORDER BY a.from_atco_code, a.to_atco_code
                """
                cursor.execute(
                    query,
                    (threshold,),
                )

                for from_code, to_code, json_data_raw in cursor:
                    json_data: list[dict[str, int]] = json_data_raw or []
                    pairs = [
                        (pair["track_a"], pair["track_b"]) for pair in json_data or []
                    ]
                    yield (from_code, to_code), pairs
        finally:
            raw_conn.close()


class TransmodelServicePatternDistanceRepo(
    BaseRepositoryWithId[TransmodelServicePatternDistance]
):
    """Repository for managing ServicePatternDistance entities"""

    def __init__(self, db: SqlDB):
        super().__init__(db, TransmodelServicePatternDistance)
