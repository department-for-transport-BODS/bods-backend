from unittest.mock import Mock, patch

import pytest
from common_layer.database.models import NaptanStopPoint, TransmodelServicePatternTracks
from common_layer.xml.txc.models import (
    TXCJourneyPattern,
)
from geoalchemy2.shape import from_shape
from shapely import Point

from tests.factories.database import NaptanStopPointFactory
from tests.factories.database.transmodel import TransmodelTracksFactory
from tests.timetables_etl.factories.txc import TXCJourneyPatternFactory
from tests.timetables_etl.factories.txc.factory_txc_service_flexible import (
    TXCFlexibleJourneyPatternFactory,
)
from timetables_etl.etl.app.helpers import TrackLookup
from timetables_etl.etl.app.transform.service_pattern_tracks import (
    generate_flexible_service_tracks,
    generate_service_pattern_tracks,
    generate_standard_service_tracks,
)


@patch(
    "timetables_etl.etl.app.transform.service_pattern_tracks.generate_standard_service_tracks"
)
def test_generate_service_pattern_tracks_standard_service(standard_service_mock: Mock):
    standard_service_mock.return_value = "return_value"
    journey_pattern: TXCJourneyPattern = TXCJourneyPatternFactory()
    tracks = generate_service_pattern_tracks(journey_pattern, 21, {}, [])
    standard_service_mock.assert_called_once()
    assert tracks == "return_value"


@patch(
    "timetables_etl.etl.app.transform.service_pattern_tracks.generate_flexible_service_tracks"
)
def test_generate_service_pattern_tracks_flexible_service(flexible_service_mock: Mock):
    flexible_service_mock.return_type = None
    journey_pattern: TXCJourneyPattern = TXCFlexibleJourneyPatternFactory()
    return_value = generate_service_pattern_tracks(journey_pattern, 21, {}, [])
    flexible_service_mock.assert_called_once()
    assert return_value == []


def test_generate_service_pattern_tracks_nonstandard_service():
    with pytest.raises(ValueError):
        generate_service_pattern_tracks("randompattern", 21, {}, [])


def test_generate_flexible_service_tracks(caplog: pytest.LogCaptureFixture):
    with caplog.at_level("ERROR"):
        generate_flexible_service_tracks(TXCFlexibleJourneyPatternFactory())


def test_generate_standard_service_tracks():
    journey_pattern = TXCJourneyPatternFactory()
    service_pattern_id = 21
    stop_sequence: list[NaptanStopPoint] = [
        NaptanStopPointFactory.create(
            atco_code="490001",
            common_name="Origin Stop",
            location=from_shape(Point(-1.0, 51.0), srid=4326),
        ),
        NaptanStopPointFactory.create(
            atco_code="490002",
            common_name="Middle Stop",
            location=from_shape(Point(-1.1, 51.1), srid=4326),
        ),
        NaptanStopPointFactory.create(
            atco_code="490003",
            common_name="Middle Stop 1",
            location=from_shape(Point(-1.2, 51.2), srid=4326),
        ),
        NaptanStopPointFactory.create(
            atco_code="490004",
            common_name="Destination Stop",
            location=from_shape(Point(-1.3, 51.3), srid=4326),
        ),
    ]
    track_lookup: TrackLookup = {
        ("490001", "490002"): TransmodelTracksFactory(
            from_atco_code="490001", to_atco_code="490002"
        ),
        ("490003", "490004"): TransmodelTracksFactory(
            from_atco_code="490003", to_atco_code="490004"
        ),
    }

    sp_tracks = generate_standard_service_tracks(
        journey_pattern, service_pattern_id, stop_sequence, track_lookup
    )

    assert len(sp_tracks) == 2
    assert isinstance(sp_tracks, list)
    assert all(isinstance(track, TransmodelServicePatternTracks) for track in sp_tracks)


def test_generate_standard_service_track_with_no_tracks():
    journey_pattern = TXCJourneyPatternFactory()
    service_pattern_id = 21
    stop_sequence: list[NaptanStopPoint] = []
    track_lookup: TrackLookup = {}

    sp_tracks = generate_standard_service_tracks(
        journey_pattern, service_pattern_id, stop_sequence, track_lookup
    )

    assert len(sp_tracks) == 0
