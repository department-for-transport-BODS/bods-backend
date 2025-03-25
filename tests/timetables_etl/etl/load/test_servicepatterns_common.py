"""
Test service patterns common functions
"""

from unittest.mock import MagicMock

import pytest
from common_layer.database.models import (
    NaptanStopPoint,
    OrganisationDatasetRevision,
    TransmodelServicePattern,
)
from common_layer.xml.txc.models import JourneyPatternVehicleDirectionT, TXCService
from geoalchemy2.shape import from_shape
from shapely import Point

from tests.factories.database import NaptanStopPointFactory
from tests.timetables_etl.factories.txc import TXCServiceFactory
from tests.timetables_etl.factories.txc.factory_txc_service import (
    TXCLineDescriptionFactory,
    TXCLineFactory,
)
from timetables_etl.etl.app.load.models_context import ProcessServicePatternContext
from timetables_etl.etl.app.load.servicepatterns_common import create_service_pattern
from timetables_etl.etl.app.transform.service_pattern_mapping import (
    ServicePatternMapping,
    ServicePatternMappingStats,
    ServicePatternMetadata,
)


@pytest.mark.parametrize(
    "direction,expected_description",
    [
        pytest.param("inbound", "Inbound Test Description", id="Inbound Direction"),
        pytest.param("outbound", "Outbound Test Description", id="Outbound Direction"),
    ],
)
def test_create_service_pattern(
    direction: JourneyPatternVehicleDirectionT, expected_description: str
):
    """Test creating a service pattern with different directions"""
    # Create service pattern ID
    service_pattern_id = "SP-TEST-123456"

    # Create stops with proper location data
    stops: list[NaptanStopPoint] = [
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
            common_name="Destination Stop",
            location=from_shape(Point(-1.2, 51.2), srid=4326),
        ),
    ]

    service: TXCService = TXCServiceFactory.create()

    # Create a TXCLine
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

    # Create the service pattern metadata
    sp_metadata = ServicePatternMetadata(
        journey_pattern_ids=["JP-1", "JP-2"],
        num_stops=len(stops),
        stop_sequence=stops,
        direction=direction,
        line_id="LINE:123",
    )

    # Create the service pattern mapping
    mapping = ServicePatternMapping(
        journey_pattern_to_service_pattern={
            "JP-1": service_pattern_id,
            "JP-2": service_pattern_id,
        },
        vehicle_journey_to_service_pattern={"VJ-1": service_pattern_id},
        service_pattern_metadata={service_pattern_id: sp_metadata},
        line_to_txc_line={"LINE:123": line},
        line_to_vehicle_journeys={"LINE:123": ["VJ-1"]},
        stats=ServicePatternMappingStats(
            service_patterns_count=1,
            journey_patterns_count=2,
            vehicle_journey_count=1,
            line_count=1,
        ),
    )

    # Create the context with a mock OrganisationDatasetRevision
    revision = MagicMock(spec=OrganisationDatasetRevision)
    revision.id = 42

    context = ProcessServicePatternContext(
        revision=revision,
        journey_pattern_sections=[],
        stop_mapping={},
        flexible_zone_lookup=None,
        db=MagicMock(),
    )

    # Call the function
    result = create_service_pattern(service, service_pattern_id, mapping, context)

    # Verify the result
    assert isinstance(result, TransmodelServicePattern)
    assert result.service_pattern_id == service_pattern_id
    assert result.origin == "Origin Stop"
    assert result.destination == "Destination Stop"
    assert result.description == expected_description
    assert result.line_name == "Test Line 123"
    assert result.revision_id == 42
    assert result.geom is not None  #
