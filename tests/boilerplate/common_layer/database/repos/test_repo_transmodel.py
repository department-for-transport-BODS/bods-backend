from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Any, Generator

from common_layer.database.client import SqlDB
from common_layer.database.dataclasses import ServiceStats
from common_layer.database.repos import TransmodelServiceRepo, TransmodelTrackRepo
from sqlalchemy import bindparam, text

from tests.factories.database import TransmodelServiceFactory


def test_service_repo_get_service_stats_by_revision_id(test_db: SqlDB):

    revision_id = 123
    repo = TransmodelServiceRepo(test_db)

    result = repo.get_service_stats_by_revision_id(revision_id)

    # No services in DB
    assert result == ServiceStats(
        first_service_start=None,
        first_expiring_service=None,
        last_expiring_service=None,
    )

    # Create services
    earliest_start_date = date(2024, 12, 1)
    earliest_end_date = date(2025, 1, 10)
    latest_end_date = date(2025, 1, 13)

    earliest_starting_service = TransmodelServiceFactory.create(
        start_date=earliest_start_date,
        end_date=datetime(2025, 1, 11),
        revision_id=revision_id,
    )
    first_expiring_service = TransmodelServiceFactory.create(
        start_date=datetime(2025, 1, 1),
        end_date=earliest_end_date,
        revision_id=revision_id,
    )
    last_expiring_service = TransmodelServiceFactory.create(
        start_date=datetime(2025, 2, 1),
        end_date=latest_end_date,
        revision_id=revision_id,
    )
    unrelated_service = TransmodelServiceFactory.create(
        start_date=datetime(2025, 2, 1),
        end_date=latest_end_date + timedelta(days=1),
        revision_id=321,
    )

    with test_db.session_scope() as session:
        session.add_all(
            [
                earliest_starting_service,
                first_expiring_service,
                last_expiring_service,
                unrelated_service,
            ]
        )
        session.commit()

    result = repo.get_service_stats_by_revision_id(revision_id)
    assert result == ServiceStats(
        first_service_start=earliest_start_date,
        first_expiring_service=earliest_end_date,
        last_expiring_service=latest_end_date,
    )


def coords_to_wkt_line(coords: list[tuple[float, float]]) -> str:
    """
    Convert a list of (lon, lat) tuples to a WKT LINESTRING
    """
    coord_str = ", ".join(f"{lon} {lat}" for lon, lat in coords)
    return f"LINESTRING({coord_str})"


def insert_track_raw(
    db: SqlDB, from_code: str, to_code: str, coords: list[tuple[float, float]]
) -> int:
    """
    Inserts a track directly using a committed connection, bypassing the test session.

    This is necessary because stream_similar_track_pairs_by_stop_points uses a raw
    named cursor, which operates outside the test session transaction.
    """
    wkt = coords_to_wkt_line(coords)
    with db.engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO transmodel_tracks (from_atco_code, to_atco_code, geometry)
                VALUES (:from_code, :to_code, ST_GeomFromText(:wkt, 4326))
                RETURNING id
            """
            ),
            {"from_code": from_code, "to_code": to_code, "wkt": wkt},
        )
        return result.scalar_one()


@contextmanager
def insert_and_cleanup_tracks(
    db: SqlDB, tracks: list[tuple[str, str, list[tuple[float, float]]]]
) -> Generator[list[Any], Any, None]:
    """
    Wrapper for ensuring inserts are cleaned up after test runs
    """
    ids: list[int] = []
    try:
        for from_code, to_code, coords in tracks:
            ids.append(insert_track_raw(db, from_code, to_code, coords))
        yield ids
    finally:
        with db.engine.begin() as conn:
            conn.execute(
                text("DELETE FROM transmodel_tracks WHERE id IN :ids").bindparams(
                    bindparam("ids", expanding=True)
                ),
                {"ids": ids},
            )


def test_transmodel_tracks_stream_similar_track_pairs_by_stop_points(
    test_db: SqlDB,
) -> None:
    # Base route geometry
    route_1_coords = [
        (-1.42148, 55.01789),
        (-1.42370, 55.01755),
        (-1.42542, 55.01784),
    ]

    route_2_coords = [
        (-1.42148, 55.01789 + 0.000169),  # offset ~19m north
        (-1.42370, 55.01755),
        (-1.42542, 55.01784),
    ]

    # Track diverges
    route_3_coords = [
        (-1.42148, 55.01789),
        (-1.42534, 55.01920),
        (-1.42542, 55.01784),
    ]
    repo = TransmodelTrackRepo(test_db)

    with insert_and_cleanup_tracks(
        test_db,
        [
            ("A", "B", route_1_coords),
            ("A", "B", route_2_coords),
            ("A", "B", route_3_coords),  # Diverging track
            ("A", "C", route_1_coords),  # Different stop points
        ],
    ) as [track1_id, similar_track_id, _, _]:
        result = list(
            repo.stream_similar_track_pairs_by_stop_points(
                stop_point_pairs=[("A", "B")], threshold=20
            )
        )

        assert len(result) == 1
        stop_point_pair, track_pairs = result[0]
        assert stop_point_pair == ("A", "B")

        assert len(track_pairs) == 1
        assert track1_id in track_pairs[0]
        assert similar_track_id in track_pairs[0]
