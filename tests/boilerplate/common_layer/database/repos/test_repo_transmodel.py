from datetime import date, datetime, timedelta

from common_layer.database.client import SqlDB
from common_layer.database.dataclasses import ServiceStats
from common_layer.database.repos import TransmodelServiceRepo, TransmodelTrackRepo
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString
from sqlalchemy import text

from tests.factories.database import TransmodelServiceFactory, TransmodelTracksFactory


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


def test_transmodel_tracks_stream_similar_track_pairs_by_stop_points(
    test_db: SqlDB,
) -> None:

    # TODO: Remove this once the unique constraint has been removed from the table # pylint: disable=fixme
    with test_db.engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE transmodel_tracks DROP CONSTRAINT IF EXISTS unique_from_to_atco_code"
            )
        )

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

    track1 = TransmodelTracksFactory.create(
        from_atco_code="A",
        to_atco_code="B",
        geometry=from_shape(LineString(route_1_coords), srid=4326),
    )
    similar_track = TransmodelTracksFactory.create(
        from_atco_code="A",
        to_atco_code="B",
        geometry=from_shape(LineString(route_2_coords), srid=4326),
    )
    different_route = TransmodelTracksFactory.create(
        from_atco_code="A",
        to_atco_code="B",
        geometry=from_shape(LineString(route_3_coords), srid=4326),
    )

    different_stop_points = TransmodelTracksFactory.create(
        from_atco_code="A",
        to_atco_code="C",
        geometry=from_shape(LineString(route_2_coords), srid=4326),
    )

    repo = TransmodelTrackRepo(test_db)

    with test_db.session_scope() as session:
        session.add_all([track1, similar_track, different_route, different_stop_points])
        session.commit()

        track1_id = track1.id
        similar_track_id = similar_track.id

        geoms = session.execute(
            text(
                """
                SELECT
                a.from_atco_code,
                a.to_atco_code,
                ST_HausdorffDistance(
                    ST_Transform(a.geometry, 27700), -- Convert to BNG for meter comparison
                    ST_Transform(b.geometry, 27700)
                )
                FROM transmodel_tracks a
                JOIN transmodel_tracks b
                ON a.from_atco_code = b.from_atco_code
                AND a.to_atco_code = b.to_atco_code
                AND a.id < b.id
                ORDER BY a.from_atco_code, a.to_atco_code;
        """
            )
        ).fetchall()

        assert geoms
        assert len(geoms) == 3

    result = list(repo.stream_similar_track_pairs_by_stop_points(21))

    assert len(result) == 1
    stop_point_pair, track_pairs = result[0]
    assert stop_point_pair == ("A", "B")

    assert set(track_pairs) == {(track1_id, similar_track_id)} or {
        (similar_track_id, track1_id)
    }
