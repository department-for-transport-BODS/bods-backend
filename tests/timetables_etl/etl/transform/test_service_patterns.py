"""
Test Generating Transmodel Service Patterns
"""

from unittest.mock import MagicMock

import pytest
from common_layer.database.models import (
    NaptanStopPoint,
    OrganisationDatasetRevision,
    TransmodelServicePattern,
)
from common_layer.xml.txc.models import (
    JourneyPatternVehicleDirectionT,
    TXCJourneyPattern,
    TXCJourneyPatternSection,
)
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape, to_shape
from shapely import Point
from shapely.geometry import LineString

from tests.factories.database import NaptanStopPointFactory
from tests.timetables_etl.factories.txc import (
    TXCJourneyPatternFactory,
    TXCJourneyPatternSectionFactory,
    TXCJourneyPatternStopUsageFactory,
    TXCJourneyPatternTimingLinkFactory,
)
from tests.timetables_etl.factories.txc.factory_txc_service import (
    TXCLineDescriptionFactory,
    TXCLineFactory,
)
from timetables_etl.etl.app.helpers.types import LookupStopPoint
from timetables_etl.etl.app.load.models_context import ProcessServicePatternContext
from timetables_etl.etl.app.transform.service_pattern_geom import (
    generate_service_pattern_geometry,
    get_valid_route_points,
)
from timetables_etl.etl.app.transform.service_pattern_mapping import (
    ServicePatternMapping,
    ServicePatternMappingStats,
    ServicePatternMetadata,
)
from timetables_etl.etl.app.transform.service_patterns import create_service_pattern


@pytest.mark.parametrize(
    "journey_pattern,sections,stop_mapping,expected_points",
    [
        pytest.param(
            TXCJourneyPatternFactory.create(
                id="JP1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSectionFactory.create(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory.create(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU1",
                                Activity="pickUpAndSetDown",
                                StopPointRef="Atco1",
                            ),
                            To=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="Atco2",
                            ),
                            RouteLinkRef="RL1",
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping_with_locations(
                [
                    ("Atco1", "Stop 1", (50.7, -3.5)),
                    ("Atco2", "Stop 2", (50.8, -3.6)),
                ]
            ),
            [(50.7, -3.5), (50.8, -3.6)],
            id="Valid points from single section",
        ),
    ],
)
def test_get_valid_route_points(
    journey_pattern: TXCJourneyPattern,
    sections: list[TXCJourneyPatternSection],
    stop_mapping: dict[str, LookupStopPoint],
    expected_points: list[tuple[float, float]],
) -> None:
    """Test getting valid route points from journey pattern sections."""
    result = get_valid_route_points(journey_pattern, sections, stop_mapping)
    assert len(result) == len(expected_points)
    for point, expected in zip(result, expected_points):
        assert point.x == expected[0]
        assert point.y == expected[1]


@pytest.mark.parametrize(
    "journey_pattern,sections,stop_mapping",
    [
        pytest.param(
            TXCJourneyPatternFactory.create(
                id="JP1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSectionFactory.create(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory.create(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU1",
                                Activity="pickUpAndSetDown",
                                StopPointRef="MissingStop1",
                            ),
                            To=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="Atco2",
                            ),
                            RouteLinkRef="RL1",
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping_with_locations(
                [
                    ("Atco2", "Stop 2", (50.8, -3.6)),
                ]
            ),
            id="Missing stop",
        ),
        pytest.param(
            TXCJourneyPatternFactory.create(
                id="JP1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSectionFactory.create(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory.create(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU1",
                                Activity="pickUpAndSetDown",
                                StopPointRef="MissingStop1",
                            ),
                            To=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="MissingStop2",
                            ),
                            RouteLinkRef="RL1",
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping_with_locations(
                [
                    ("Atco3", "Stop 3", (50.9, -3.7)),
                ]
            ),
            id="All stops missing",
        ),
    ],
)
def test_get_valid_route_points_error(journey_pattern, sections, stop_mapping) -> None:
    """Test that a ValueError is raised when any stop points are missing."""
    with pytest.raises(
        ValueError,
        match="Stop referenced in JourneyPatternSections not found in stop map",
    ):
        get_valid_route_points(journey_pattern, sections, stop_mapping)


@pytest.mark.parametrize(
    "journey_pattern,sections,stop_mapping,expected_result",
    [
        pytest.param(
            TXCJourneyPatternFactory.create(
                id="JP1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSectionFactory.create(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory.create(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU1",
                                Activity="pickUpAndSetDown",
                                StopPointRef="Atco1",
                            ),
                            To=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="Atco2",
                            ),
                            RouteLinkRef="RL1",
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping_with_locations(
                [
                    ("Atco1", "Stop 1", (50.7, -3.5)),
                    ("Atco2", "Stop 2", (50.8, -3.6)),
                ]
            ),
            [(50.7, -3.5), (50.8, -3.6)],
            id="Valid service pattern",
        ),
    ],
)
def test_generate_service_pattern_geometry(
    journey_pattern: TXCJourneyPattern,
    sections: list[TXCJourneyPatternSection],
    stop_mapping: dict[str, LookupStopPoint],
    expected_result: list[tuple[float, float]],
) -> None:
    """Test generating the LineString from the JourneyPatternSections."""

    result = generate_service_pattern_geometry(journey_pattern, sections, stop_mapping)

    assert isinstance(result, WKBElement)
    line = to_shape(result)
    assert isinstance(line, LineString)
    assert len(line.coords) == len(expected_result)

    for actual, expected in zip(line.coords, expected_result):
        assert actual == expected


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
        db=MagicMock(),
    )

    # Call the function
    result = create_service_pattern(service_pattern_id, mapping, context)

    # Verify the result
    assert isinstance(result, TransmodelServicePattern)
    assert result.service_pattern_id == service_pattern_id
    assert result.origin == "Origin Stop"
    assert result.destination == "Destination Stop"
    assert result.description == expected_description
    assert result.line_name == "Test Line 123"
    assert result.revision_id == 42
    assert result.geom is not None  #
