"""
Test Generating Transmodel Service Patterns
"""

from datetime import date
from typing import Callable

import pytest
from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from shapely import Point
from shapely.geometry import LineString

from tests.timetables_etl.factories.database.naptan import NaptanStopPointFactory
from timetables_etl.etl.app.database.models.model_naptan import NaptanStopPoint
from timetables_etl.etl.app.database.models.model_transmodel import (
    TransmodelServicePattern,
)
from timetables_etl.etl.app.transform.service_patterns import (
    LineDescription,
    PatternMetadata,
    create_service_pattern,
    extract_pattern_metadata,
    generate_service_pattern_geometry,
    get_line_description,
)
from timetables_etl.etl.app.txc.models.txc_journey_pattern import (
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
)
from timetables_etl.etl.app.txc.models.txc_service import (
    TXCJourneyPattern,
    TXCLine,
    TXCLineDescription,
    TXCService,
    TXCStandardService,
)


@pytest.mark.parametrize(
    "line,direction,expected",
    [
        pytest.param(
            TXCLine(
                id="1",
                LineName="Test Line",
                InboundDescription=TXCLineDescription(
                    Origin="Start", Destination="End", Description="Start to End Route"
                ),
            ),
            "inbound",
            LineDescription(
                origin="Start", destination="End", description="Start to End Route"
            ),
            id="Valid: Inbound",
        ),
        pytest.param(
            TXCLine(
                id="1",
                LineName="Test Line",
                OutboundDescription=TXCLineDescription(
                    Origin="End", Destination="Start", Description="End to Start Route"
                ),
            ),
            "outbound",
            LineDescription(
                origin="End", destination="Start", description="End to Start Route"
            ),
            id="Valid: Outbound",
        ),
        pytest.param(
            TXCLine(id="1", LineName="Test Line"),
            "inbound",
            None,
            id="Missing Description: Inbound",
        ),
        pytest.param(
            TXCLine(id="1", LineName="Test Line"),
            "outbound",
            None,
            id="Missing Description: Outbound",
        ),
    ],
)
def test_get_line_description(
    line: TXCLine, direction: str, expected: LineDescription | None
) -> None:
    """
    Test Generating line description from a TXCLine based on direction
    """
    result = get_line_description(line, direction)
    assert result == expected


@pytest.mark.parametrize(
    "service,journey_pattern,sections,stop_mapping,expected",
    [
        pytest.param(
            TXCService(
                RevisionNumber=1,
                ServiceCode="UZ000FLIX:UK045",
                PrivateCode="UK045",
                RegisteredOperatorRef="FLIX",
                PublicUse=True,
                StartDate=date(2024, 11, 11),
                EndDate=date(2025, 1, 5),
                StandardService=TXCStandardService(
                    Origin="London",
                    Destination="Plymouth",
                    JourneyPattern=[],
                ),
                FlexibleService=None,
                Lines=[
                    TXCLine(
                        id="FLIX:UZ000FLIX:UK045:UK045",
                        LineName="UK045",
                        MarketingName=None,
                        OutboundDescription=TXCLineDescription(
                            Origin="London",
                            Destination="Plymouth",
                            Description="London - Plymouth",
                        ),
                        InboundDescription=TXCLineDescription(
                            Origin="Plymouth",
                            Destination="London",
                            Description="Plymouth - London",
                        ),
                    )
                ],
                Mode="coach",
            ),
            TXCJourneyPattern(
                id="JP1",
                DestinationDisplay="Victoria - Plymouth",
                Direction="inbound",
                RouteRef="R1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSection(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                Activity="pickUp",
                                StopPointRef="490014051VC",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="118000037",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="RL1",
                            RunTime="PT0H0M0S",
                        ),
                    ],
                )
            ],
            NaptanStopPointFactory.create_mapping(
                [
                    ("490014051VC", "Victoria Coach Station"),
                    ("118000037", "Plymouth Coach Station"),
                ]
            ),
            PatternMetadata(
                origin="Plymouth",
                destination="London",
                description="Plymouth - London",
                line_name="UK045",
            ),
            id="Using Line Description",
        ),
        pytest.param(
            TXCService(
                RevisionNumber=1,
                ServiceCode="UZ000FLIX:UK045",
                PrivateCode="UK045",
                RegisteredOperatorRef="FLIX",
                PublicUse=True,
                StartDate=date(2024, 11, 11),
                EndDate=date(2025, 1, 5),
                StandardService=TXCStandardService(
                    Origin="London",
                    Destination="Plymouth",
                    JourneyPattern=[],
                ),
                FlexibleService=None,
                Lines=[],
                Mode="coach",
            ),
            TXCJourneyPattern(
                id="JP1",
                DestinationDisplay="Victoria - Plymouth",
                Direction="inbound",
                RouteRef="R1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSection(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                Activity="pickUp",
                                StopPointRef="490014051VC",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="118000037",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="RL1",
                            RunTime="PT0H0M0S",
                        ),
                    ],
                )
            ],
            NaptanStopPointFactory.create_mapping(
                [
                    ("490014051VC", "Victoria Coach Station"),
                    ("118000037", "Plymouth Coach Station"),
                ]
            ),
            PatternMetadata(
                origin="Victoria Coach Station",
                destination="Plymouth Coach Station",
                description="Victoria Coach Station - Plymouth Coach Station",
                line_name="unknown",
            ),
            id="Using Stop Common Name: No Lines Available",
        ),
        pytest.param(
            TXCService(
                RevisionNumber=1,
                ServiceCode="UZ000FLIX:UK045",
                PrivateCode="UK045",
                RegisteredOperatorRef="FLIX",
                PublicUse=True,
                StartDate=date(2024, 11, 11),
                EndDate=date(2025, 1, 5),
                StandardService=TXCStandardService(
                    Origin="London",
                    Destination="Plymouth",
                    JourneyPattern=[],
                ),
                FlexibleService=None,
                Lines=[
                    TXCLine(
                        id="FLIX:UZ000FLIX:UK045:UK045",
                        LineName="UK045",
                        MarketingName=None,
                        OutboundDescription=None,
                        InboundDescription=None,
                    )
                ],
                Mode="coach",
            ),
            TXCJourneyPattern(
                id="JP1",
                DestinationDisplay="Victoria - Plymouth",
                Direction="inbound",
                RouteRef="R1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSection(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                Activity="pickUp",
                                StopPointRef="490014051VC",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="118000037",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="RL1",
                            RunTime="PT0H0M0S",
                        ),
                    ],
                )
            ],
            NaptanStopPointFactory.create_mapping(
                [
                    ("490014051VC", "Victoria Coach Station"),
                    ("118000037", "Plymouth Coach Station"),
                ]
            ),
            PatternMetadata(
                origin="Victoria Coach Station",
                destination="Plymouth Coach Station",
                description="Victoria Coach Station - Plymouth Coach Station",
                line_name="UK045",
            ),
            id="Using Stop Common Name: No Line Description",
        ),
    ],
)
def test_extract_pattern_metadata(
    service: TXCService,
    journey_pattern: TXCJourneyPattern,
    sections: list[TXCJourneyPatternSection],
    stop_mapping: dict[str, NaptanStopPoint],
    expected: PatternMetadata,
) -> None:
    """
    Testing extracting the Origin / Destination / Description for a Service Pattern

    """
    result = extract_pattern_metadata(service, journey_pattern, sections, stop_mapping)
    assert result == expected


@pytest.mark.parametrize(
    "journey_pattern,sections,stop_mapping,expected_coordinates",
    [
        pytest.param(
            TXCJourneyPattern(
                id="JP1",
                DestinationDisplay="Test Route",
                Direction="inbound",
                RouteRef="R1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSection(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                Activity="pickUpAndSetDown",
                                StopPointRef="Atco1",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="Atco2",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="RL1",
                            RunTime="PT0H0M0S",
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
            id="Single JourneyPatternSection for JourneyPattern",
        ),
        pytest.param(
            TXCJourneyPattern(
                id="JP1",
                DestinationDisplay="Test Route",
                Direction="inbound",
                RouteRef="R1",
                JourneyPatternSectionRefs=["JPS1", "JPS2"],
            ),
            [
                TXCJourneyPatternSection(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                Activity="pickUp",
                                StopPointRef="Atco1",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                Activity="pickUpAndSetDown",
                                StopPointRef="Atco2",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="RL1",
                            RunTime="PT0H0M0S",
                        ),
                    ],
                ),
                TXCJourneyPatternSection(
                    id="JPS2",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL2",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU3",
                                Activity="pickUpAndSetDown",
                                StopPointRef="Atco2",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU4",
                                Activity="setDown",
                                StopPointRef="Atco3",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="RL2",
                            RunTime="PT0H0M0S",
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
    Test generating the LineString from the JourneyPatternSections for a JourneyPattern
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
            TXCService(
                RevisionNumber=1,
                ServiceCode="UZ000FLIX:UK045",
                PrivateCode="UK045",
                RegisteredOperatorRef="FLIX",
                PublicUse=True,
                StartDate=date(2024, 11, 11),
                EndDate=date(2025, 1, 5),
                StandardService=TXCStandardService(
                    Origin="London",
                    Destination="Plymouth",
                    JourneyPattern=[],
                ),
                FlexibleService=None,
                Lines=[
                    TXCLine(
                        id="FLIX:UZ000FLIX:UK045:UK045",
                        LineName="UK045",
                        MarketingName=None,
                        OutboundDescription=TXCLineDescription(
                            Origin="London",
                            Destination="Plymouth",
                            Description="London - Plymouth",
                        ),
                        InboundDescription=TXCLineDescription(
                            Origin="Plymouth",
                            Destination="London",
                            Description="Plymouth - London",
                        ),
                    )
                ],
                Mode="coach",
            ),
            TXCJourneyPattern(
                id="JP1",
                DestinationDisplay="Victoria - Plymouth",
                Direction="outbound",
                RouteRef="R1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSection(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                Activity="pickUp",
                                StopPointRef="490014051VC",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="118000037",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="RL1",
                            RunTime="PT0H0M0S",
                        ),
                    ],
                )
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
            TXCService(
                RevisionNumber=1,
                ServiceCode="UZ000FLIX:UK045",
                PrivateCode="UK045",
                RegisteredOperatorRef="FLIX",
                PublicUse=True,
                StartDate=date(2024, 11, 11),
                EndDate=date(2025, 1, 5),
                StandardService=TXCStandardService(
                    Origin="London",
                    Destination="Plymouth",
                    JourneyPattern=[],
                ),
                FlexibleService=None,
                Lines=[],
                Mode="coach",
            ),
            TXCJourneyPattern(
                id="JP1",
                DestinationDisplay="Victoria - Plymouth",
                Direction="outbound",
                RouteRef="R1",
                JourneyPatternSectionRefs=["JPS1"],
            ),
            [
                TXCJourneyPatternSection(
                    id="JPS1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="JPTL1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                Activity="pickUp",
                                StopPointRef="490014051VC",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                Activity="setDown",
                                StopPointRef="118000037",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="RL1",
                            RunTime="PT0H0M0S",
                        ),
                    ],
                )
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
    organisation_dataset_revision,
    service: TXCService,
    journey_pattern: TXCJourneyPattern,
    sections: list[TXCJourneyPatternSection],
    stop_mapping: dict[str, NaptanStopPoint],
    expected_pattern: Callable,
) -> None:
    """
    Test creating a TransmodelServicePattern from TXC data
    """
    result = create_service_pattern(
        service,
        journey_pattern,
        organisation_dataset_revision,
        sections,
        stop_mapping,
    )

    # Test pattern matches expected values
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
