"""
Test Generating Transmodel Service Patterns
"""

from typing import Callable

import pytest
from common_layer.database.models import NaptanStopPoint, TransmodelServicePattern
from common_layer.txc.models import (
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCService,
)
from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from shapely import Point
from shapely.geometry import LineString

from tests.factories.database import (
    NaptanStopPointFactory,
    OrganisationDatasetRevisionFactory,
)
from tests.timetables_etl.factories.txc import (
    TXCJourneyPatternFactory,
    TXCJourneyPatternSectionFactory,
    TXCJourneyPatternStopUsageFactory,
    TXCJourneyPatternTimingLinkFactory,
    TXCServiceFactory,
)
from timetables_etl.etl.app.transform.service_patterns import (
    create_service_pattern,
    generate_service_pattern_geometry,
)


@pytest.mark.parametrize(
    "journey_pattern,sections,stop_mapping,expected_coordinates",
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
            id="Single JourneyPatternSection",
        ),
        pytest.param(
            TXCJourneyPatternFactory.create(
                id="JP1",
                JourneyPatternSectionRefs=["JPS1", "JPS2"],
            ),
            [
                TXCJourneyPatternSectionFactory.create(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory.create(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU1",
                                Activity="pickUp",
                                StopPointRef="Atco1",
                            ),
                            To=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU2",
                                Activity="pickUpAndSetDown",
                                StopPointRef="Atco2",
                            ),
                            RouteLinkRef="RL1",
                        ),
                    ],
                ),
                TXCJourneyPatternSectionFactory.create(
                    id="JPS2",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLinkFactory.create(
                            id="JPTL2",
                            From=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU3",
                                Activity="pickUpAndSetDown",
                                StopPointRef="Atco2",
                            ),
                            To=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU4",
                                Activity="setDown",
                                StopPointRef="Atco3",
                            ),
                            RouteLinkRef="RL2",
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping_with_locations(
                [
                    ("Atco1", "Stop 1", (50.7, -3.5)),
                    ("Atco2", "Stop 2", (50.8, -3.6)),
                    ("Atco3", "Stop 3", (50.9, -3.7)),
                ]
            ),
            [(50.7, -3.5), (50.8, -3.6), (50.9, -3.7)],
            id="Multiple JourneyPatternSections",
        ),
    ],
)
def test_generate_service_pattern_geometry(
    journey_pattern: TXCJourneyPattern,
    sections: list[TXCJourneyPatternSection],
    stop_mapping: dict[str, NaptanStopPoint],
    expected_coordinates: list[tuple[float, float]],
) -> None:
    """
    Test generating the LineString from the JourneyPatternSections for a JourneyPattern.

    """
    result = generate_service_pattern_geometry(journey_pattern, sections, stop_mapping)
    assert isinstance(result, WKBElement)

    line = to_shape(result)
    assert len(line.coords) == len(expected_coordinates)
    for actual, expected in zip(line.coords, expected_coordinates):
        assert actual == expected


@pytest.mark.parametrize(
    "service,journey_pattern,sections,stop_mapping,expected_pattern",
    [
        pytest.param(
            TXCServiceFactory.create(with_standard_line=True),
            TXCJourneyPatternFactory.create(
                id="JP1",
                Direction="outbound",
                DestinationDisplay="Victoria - Plymouth",
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
                                Activity="pickUp",
                                StopPointRef="490014051VC",
                            ),
                            To=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="118000037",
                            ),
                            RouteLinkRef="RL1",
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping_with_locations(
                [
                    ("490014051VC", "Victoria Coach Station", (51.4945, -0.1447)),
                    ("118000037", "Plymouth Coach Station", (50.3754, -4.1426)),
                ]
            ),
            lambda pattern: TransmodelServicePattern(
                service_pattern_id=pattern.service_pattern_id,
                origin="London",
                destination="Plymouth",
                description="London - Plymouth",
                revision_id=pattern.revision_id,
                line_name="UK045",
                geom=pattern.geom,
            ),
            id="Valid Service Pattern with Line Description",
        ),
        pytest.param(
            TXCServiceFactory.create(no_lines=True),
            TXCJourneyPatternFactory.create(
                id="JP1",
                Direction="outbound",
                DestinationDisplay="Victoria - Plymouth",
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
                                Activity="pickUp",
                                StopPointRef="490014051VC",
                            ),
                            To=TXCJourneyPatternStopUsageFactory.create(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="118000037",
                            ),
                            RouteLinkRef="RL1",
                        ),
                    ],
                ),
            ],
            NaptanStopPointFactory.create_mapping_with_locations(
                [
                    ("490014051VC", "Victoria Coach Station", (51.4945, -0.1447)),
                    ("118000037", "Plymouth Coach Station", (50.3754, -4.1426)),
                ]
            ),
            lambda pattern: TransmodelServicePattern(
                service_pattern_id=pattern.service_pattern_id,
                origin="Victoria Coach Station",
                destination="Plymouth Coach Station",
                description="Victoria Coach Station - Plymouth Coach Station",
                revision_id=pattern.revision_id,
                line_name="unknown",
                geom=pattern.geom,
            ),
            id="Service Pattern without Lines using Stop Names",
        ),
    ],
)
def test_create_service_pattern(
    service: TXCService,
    journey_pattern: TXCJourneyPattern,
    sections: list[TXCJourneyPatternSection],
    stop_mapping: dict[str, NaptanStopPoint],
    expected_pattern: Callable[[TransmodelServicePattern], TransmodelServicePattern],
) -> None:
    """
    Test creating a TransmodelServicePattern from TXC data.

    """
    organisation_dataset_revision = OrganisationDatasetRevisionFactory.create_with_id(1)
    result = create_service_pattern(
        service,
        journey_pattern,
        organisation_dataset_revision,
        sections,
        stop_mapping,
    )

    expected = expected_pattern(result)
    assert isinstance(result, TransmodelServicePattern)
    assert result.origin == expected.origin
    assert result.destination == expected.destination
    assert result.description == expected.description
    assert result.line_name == expected.line_name
    assert result.revision_id == organisation_dataset_revision.id

    # Validate geometry
    assert isinstance(result.geom, WKBElement)
    result_line = to_shape(result.geom)
    expected_line = LineString(
        [
            Point(to_shape(stop_mapping[stop.StopPointRef].location).coords[0])
            for link in sections[0].JourneyPatternTimingLink
            for stop in [link.From, link.To]
        ]
    )
    assert list(result_line.coords) == list(expected_line.coords)
