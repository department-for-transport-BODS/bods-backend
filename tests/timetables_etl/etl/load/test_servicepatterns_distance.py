from unittest.mock import MagicMock, create_autospec, patch

import pytest
from common_layer.database import SqlDB
from common_layer.database.models import NaptanStopPoint, TransmodelTracks
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape  # type: ignore
from shapely import Point
from shapely.geometry import LineString

from tests.factories.database.naptan import NaptanStopPointFactory
from tests.factories.database.transmodel import TransmodelTracksFactory
from timetables_etl.etl.app.helpers import TrackLookup
from timetables_etl.etl.app.load.servicepatterns_distance import (
    get_geometry_and_distance_from_tracks,
    has_sufficient_track_data,
    process_service_pattern_distance,
)


@pytest.fixture
def stop_sequence() -> list[NaptanStopPoint]:
    return [
        NaptanStopPointFactory.create(
            atco_code="A", location=from_shape(Point(0, 0), srid=4326)
        ),
        NaptanStopPointFactory.create(
            atco_code="B", location=from_shape(Point(0.01, 0.01), srid=4326)
        ),
        NaptanStopPointFactory.create(
            atco_code="C", location=from_shape(Point(0.02, 0.02), srid=4326)
        ),
    ]


@pytest.fixture
def sufficient_tracks() -> TrackLookup:
    return {
        ("A", "B"): TransmodelTracksFactory.create(
            from_atco_code="A",
            to_atco_code="B",
            geometry=from_shape(
                LineString([(0, 0), (0.005, 0.005), (0.01, 0.01)]), srid=4326
            ),
            distance=100,
            coord_distance=120,
        ),
        ("B", "C"): TransmodelTracksFactory.create(
            from_atco_code="B",
            to_atco_code="C",
            geometry=from_shape(
                LineString([(0.01, 0.01), (0.015, 0.015), (0.02, 0.02)]), srid=4326
            ),
            distance=150,
            coord_distance=90,
        ),
        # Track from another RouteSection
        # (should not be used because its not in stop_sequence)
        ("C", "D"): TransmodelTracksFactory.create(
            from_atco_code="C",
            to_atco_code="D",
            geometry=from_shape(
                LineString([(0.01, 0.01), (0.015, 0.015), (0.02, 0.02)]), srid=4326
            ),
            distance=150,
            coord_distance=110,
        ),
    }


def test_has_sufficient_track_data_true(
    sufficient_tracks: TrackLookup,
    stop_sequence: list[NaptanStopPoint],
) -> None:
    assert has_sufficient_track_data(sufficient_tracks, stop_sequence) is True


@pytest.mark.parametrize(
    "tracks",
    [
        pytest.param(
            {
                # Missing B->C track
                ("A", "B"): TransmodelTracksFactory.create(
                    from_atco_code="A",
                    to_atco_code="B",
                    geometry=from_shape(
                        LineString([(0, 0), (0.005, 0.005), (0.01, 0.01)]),
                        srid=4326,
                    ),
                    distance=100,
                    coord_distance=120,
                ),
            },
            id="missing-track-between-stops",
        ),
        pytest.param(
            {
                # A->B track has only 2 points
                ("A", "B"): TransmodelTracksFactory.create(
                    from_atco_code="A",
                    to_atco_code="B",
                    geometry=from_shape(
                        LineString([(0, 0), (0.005, 0.005)]), srid=4326
                    ),
                    distance=100,
                    coord_distance=120,
                ),
                ("B", "C"): TransmodelTracksFactory.create(
                    from_atco_code="B",
                    to_atco_code="C",
                    geometry=from_shape(
                        LineString([(0.01, 0.01), (0.015, 0.015), (0.02, 0.02)]),
                        srid=4326,
                    ),
                    distance=100,
                    coord_distance=90,
                ),
            },
            id="insufficient-points-in-track-geometry",
        ),
    ],
)
def test_has_sufficient_track_data_insufficient_cases(
    tracks: TrackLookup,
    stop_sequence: list[NaptanStopPoint],
) -> None:
    assert has_sufficient_track_data(tracks, stop_sequence) is False


def test_get_geometry_and_distance_from_tracks(
    sufficient_tracks: TrackLookup, stop_sequence: list[NaptanStopPoint]
) -> None:
    geom, total_coord_distance, distance = get_geometry_and_distance_from_tracks(
        sufficient_tracks, stop_sequence
    )
    assert isinstance(geom, WKBElement)
    assert distance == 250, "total distance = 100 + 150"
    assert total_coord_distance == 210


@patch(
    "timetables_etl.etl.app.load.servicepatterns_distance.TransmodelServicePatternDistanceRepo"
)
@patch("timetables_etl.etl.app.load.servicepatterns_distance.OSRMGeometryAPI")
def test_process_service_pattern_distance_uses_tracks_data_when_sufficient(
    m_geometry_api: MagicMock,
    m_distance_repo: MagicMock,
    sufficient_tracks: dict[tuple[str, str], TransmodelTracks],
    stop_sequence: list[NaptanStopPoint],
) -> None:
    mock_service = MagicMock()
    mock_service.FlexibleService = False
    mock_db = create_autospec(SqlDB, instance=True)

    expected_distance = 250  # 2 tracks, distances 100 + 150
    expected_coord_distance = 210  # 2 tracks, coord distance 120 + 90

    distance = process_service_pattern_distance(
        service=mock_service,
        service_pattern_id=123,
        tracks=sufficient_tracks,
        stop_sequence=stop_sequence,
        db=mock_db,
    )

    assert distance == expected_distance
    m_geometry_api.return_value.get_geometry_and_distance.assert_not_called()

    insert_args, _ = m_distance_repo.return_value.insert.call_args
    inserted_obj = insert_args[0]
    assert inserted_obj.service_pattern_id == 123
    assert inserted_obj.distance == expected_distance
    assert inserted_obj.coord_track_distance == expected_coord_distance
    assert isinstance(inserted_obj.geom, WKBElement)


@patch(
    "timetables_etl.etl.app.load.servicepatterns_distance.TransmodelServicePatternDistanceRepo"
)
@patch("timetables_etl.etl.app.load.servicepatterns_distance.OSRMGeometryAPI")
def test_process_service_pattern_distance_uses_osrm_geom_api(
    m_geometry_api: MagicMock,
    m_distance_repo: MagicMock,
    stop_sequence: list[NaptanStopPoint],
) -> None:
    mock_service = MagicMock()
    mock_service.FlexibleService = False
    mock_db = create_autospec(SqlDB, instance=True)

    expected_coords = [(stop.shape.x, stop.shape.y) for stop in stop_sequence]
    mock_geom = from_shape(LineString(expected_coords), srid=4326)
    m_geometry_api.return_value.get_geometry_and_distance.return_value = (
        mock_geom,
        1234,
    )
    expected_distance = 1234

    distance = process_service_pattern_distance(
        service=mock_service,
        service_pattern_id=123,
        tracks={},  # no tracks
        stop_sequence=stop_sequence,
        db=mock_db,
    )

    assert distance == expected_distance
    m_geometry_api.return_value.get_geometry_and_distance.assert_called_once_with(
        expected_coords
    )
    insert_args, _ = m_distance_repo.return_value.insert.call_args
    inserted_obj = insert_args[0]
    assert inserted_obj.service_pattern_id == 123
    assert inserted_obj.distance == expected_distance
    assert inserted_obj.coord_track_distance is None
    assert inserted_obj.geom == mock_geom


@patch(
    "timetables_etl.etl.app.load.servicepatterns_distance.TransmodelServicePatternDistanceRepo"
)
@patch("timetables_etl.etl.app.load.servicepatterns_distance.OSRMGeometryAPI")
def test_process_service_pattern_distance_skips_creation_for_flexible_services(
    m_geometry_api: MagicMock,
    m_distance_repo: MagicMock,
    sufficient_tracks: dict[tuple[str, str], TransmodelTracks],
    stop_sequence: list[NaptanStopPoint],
) -> None:
    mock_service = MagicMock()
    mock_service.FlexibleService = True
    mock_db = create_autospec(SqlDB, instance=True)

    distance = process_service_pattern_distance(
        service=mock_service,
        service_pattern_id=123,
        tracks=sufficient_tracks,
        stop_sequence=stop_sequence,
        db=mock_db,
    )
    assert distance is None
    m_distance_repo.return_value.insert.assert_not_called()
