"""
Test Generating Transmodel Service Patterns
"""

import pytest
from common_layer.xml.txc.models import TXCJourneyPattern, TXCJourneyPatternSection
from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry import LineString

from tests.factories.database import NaptanStopPointFactory
from tests.timetables_etl.factories.txc import (
    TXCJourneyPatternFactory,
    TXCJourneyPatternSectionFactory,
    TXCJourneyPatternStopUsageFactory,
    TXCJourneyPatternTimingLinkFactory,
)
from timetables_etl.etl.app.helpers.types import LookupStopPoint
from timetables_etl.etl.app.transform.service_pattern_geom import (
    generate_service_pattern_geometry,
    get_valid_route_points,
)


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
