"""
Test Creating Metadata
"""

import pytest
from common_layer.database.models.model_naptan import NaptanStopPoint
from common_layer.xml.txc.models.txc_types import JourneyPatternVehicleDirectionT
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from tests.factories.database.naptan import NaptanStopPointFactory
from tests.timetables_etl.factories.txc.factory_txc_service import (
    TXCLineDescriptionFactory,
    TXCLineFactory,
)
from timetables_etl.etl.app.transform.service_pattern_mapping import (
    ServicePatternMetadata,
)
from timetables_etl.etl.app.transform.service_pattern_metadata import (
    PatternMetadata,
    make_metadata,
)


@pytest.mark.parametrize(
    "direction,line_id,expected_description",
    [
        pytest.param(
            "inbound", "LINE:123", "Inbound Test Description", id="Inbound with Line"
        ),
        pytest.param(
            "outbound", "LINE:123", "Outbound Test Description", id="Outbound with Line"
        ),
        pytest.param(
            "clockwise",
            "LINE:123",
            "Outbound Test Description",
            id="clockwise with Line",
        ),
        pytest.param(
            "antiClockwise",
            "LINE:123",
            "Inbound Test Description",
            id="antiClockwise with Line",
        ),
        pytest.param("inbound", "NONEXISTENT_LINE", "unknown", id="Missing Line"),
    ],
)
def test_make_metadata(
    direction: str, line_id: str, expected_description: JourneyPatternVehicleDirectionT
):
    """Test make_metadata with different directions and line scenarios"""
    # Create stops with proper location data
    stops: list[NaptanStopPoint] = [
        NaptanStopPointFactory.create(
            atco_code="490001",
            common_name="First Stop",
            location=from_shape(Point(-1.0, 51.0), srid=4326),
        ),
        NaptanStopPointFactory.create(
            atco_code="490002",
            common_name="Middle Stop",
            location=from_shape(Point(-1.1, 51.1), srid=4326),
        ),
        NaptanStopPointFactory.create(
            atco_code="490003",
            common_name="Last Stop",
            location=from_shape(Point(-1.2, 51.2), srid=4326),
        ),
    ]

    line = TXCLineFactory.create(
        id="LINE:123",
        LineName="Test Line 123",
        InboundDescription=TXCLineDescriptionFactory.create(
            Description="Inbound Test Description"
        ),
        OutboundDescription=TXCLineDescriptionFactory.create(
            Description="Outbound Test Description"
        ),
    )

    sp_data = ServicePatternMetadata(
        journey_pattern_ids=["JP-1", "JP-2"],
        num_stops=len(stops),
        stop_sequence=stops,
        direction=direction,  # type: ignore
        line_id=line_id,
    )

    line_to_txc_line = {"LINE:123": line}

    result = make_metadata(sp_data, line_to_txc_line)

    # Verify result
    assert isinstance(result, PatternMetadata)
    assert result.origin == "First Stop"
    assert result.destination == "Last Stop"
    assert result.line_name == "Test Line 123" if line_id == "LINE:123" else "unknown"
    assert result.description == expected_description
