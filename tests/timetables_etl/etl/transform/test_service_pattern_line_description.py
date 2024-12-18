"""
Tests for getting service pattern line description
"""

from datetime import date

import pytest
from common_layer.database.models import NaptanStopPoint
from common_layer.txc.models import (
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
    TXCLine,
    TXCLineDescription,
    TXCService,
    TXCStandardService,
)

from tests.timetables_etl.factories.database.naptan import NaptanStopPointFactory
from tests.timetables_etl.factories.txc import TXCLineDescriptionFactory, TXCLineFactory
from timetables_etl.etl.app.transform.service_pattern_metadata import (
    LineDescription,
    PatternMetadata,
    extract_pattern_metadata,
    get_line_description,
)


@pytest.mark.parametrize(
    "line,direction,expected",
    [
        pytest.param(
            TXCLineFactory.create(
                LineName="UK045",
                with_descriptions=True,
            ),
            "inbound",
            LineDescription(
                origin="Plymouth",
                destination="London",
                description="Plymouth - London",
            ),
            id="Valid: Inbound Line Description",
        ),
        pytest.param(
            TXCLineFactory.create(
                LineName="UK045",
                with_descriptions=True,
            ),
            "outbound",
            LineDescription(
                origin="London",
                destination="Plymouth",
                description="London - Plymouth",
            ),
            id="Valid: Outbound Line Description",
        ),
        pytest.param(
            TXCLineFactory.create(
                LineName="UK045",
                OutboundDescription=None,
                InboundDescription=None,
            ),
            "inbound",
            None,
            id="Missing Both Descriptions: Inbound",
        ),
        pytest.param(
            TXCLineFactory.create(
                LineName="UK045",
                OutboundDescription=None,
                InboundDescription=None,
            ),
            "outbound",
            None,
            id="Missing Both Descriptions: Outbound",
        ),
        pytest.param(
            TXCLineFactory.create(
                LineName="UK045",
                OutboundDescription=TXCLineDescriptionFactory.create(outbound=True),
                InboundDescription=None,
            ),
            "inbound",
            None,
            id="Missing Inbound Description",
        ),
        pytest.param(
            TXCLineFactory.create(
                LineName="UK045",
                OutboundDescription=None,
                InboundDescription=TXCLineDescriptionFactory.create(inbound=True),
            ),
            "outbound",
            None,
            id="Missing Outbound Description",
        ),
        pytest.param(
            TXCLineFactory.create(
                LineName="UK045",
                OutboundDescription=TXCLineDescriptionFactory.create(
                    outbound=True,
                    Description="Custom outbound description",
                ),
                InboundDescription=TXCLineDescriptionFactory.create(
                    inbound=True,
                    Description="Custom inbound description",
                ),
            ),
            "outbound",
            LineDescription(
                origin="London",
                destination="Plymouth",
                description="Custom outbound description",
            ),
            id="Custom Description Text",
        ),
    ],
)
def test_get_line_description(
    line: TXCLine,
    direction: str,
    expected: LineDescription | None,
) -> None:
    """
    Test getting line descriptions based on direction.

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
