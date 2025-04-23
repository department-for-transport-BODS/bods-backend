"""
Test Parsing Funtions for xml of journey pattern sections
"""

import pytest
from common_layer.xml.txc.models import (
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
)
from common_layer.xml.txc.parser.journey_pattern_sections import (
    parse_journey_pattern_section,
    parse_journey_pattern_sections,
)
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <JourneyPatternSection id="jps1">
                <JourneyPatternTimingLink id="tl1">
                    <From id="JPSU1">
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp1</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                    </From>
                    <To id="JPSU2">
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp2</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                    </To>
                    <RouteLinkRef>rl1</RouteLinkRef>
                    <RunTime>PT5M</RunTime>
                    <Distance>1000</Distance>
                </JourneyPatternTimingLink>
                <JourneyPatternTimingLink id="tl2">
                    <From id="JPSU3">
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp2</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                    </From>
                    <To id="JPSU4">
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp3</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                    </To>
                    <RouteLinkRef>rl2</RouteLinkRef>
                    <RunTime>PT10M</RunTime>
                    <Distance>2000</Distance>
                </JourneyPatternTimingLink>
            </JourneyPatternSection>
            """,
            TXCJourneyPatternSection(
                id="jps1",
                JourneyPatternTimingLink=[
                    TXCJourneyPatternTimingLink(
                        id="tl1",
                        From=TXCJourneyPatternStopUsage(
                            id="JPSU1",
                            Activity="pickUpAndSetDown",
                            StopPointRef="sp1",
                            TimingStatus="principalTimingPoint",
                        ),
                        To=TXCJourneyPatternStopUsage(
                            id="JPSU2",
                            Activity="pickUpAndSetDown",
                            StopPointRef="sp2",
                            TimingStatus="principalTimingPoint",
                        ),
                        RouteLinkRef="rl1",
                        RunTime="PT5M",
                        Distance="1000",
                    ),
                    TXCJourneyPatternTimingLink(
                        id="tl2",
                        From=TXCJourneyPatternStopUsage(
                            id="JPSU3",
                            Activity="pickUpAndSetDown",
                            StopPointRef="sp2",
                            TimingStatus="principalTimingPoint",
                        ),
                        To=TXCJourneyPatternStopUsage(
                            id="JPSU4",
                            Activity="pickUpAndSetDown",
                            StopPointRef="sp3",
                            TimingStatus="principalTimingPoint",
                        ),
                        RouteLinkRef="rl2",
                        RunTime="PT10M",
                        Distance="2000",
                    ),
                ],
            ),
            id="Valid",
        ),
        pytest.param(
            """
            <JourneyPatternSection>
                <JourneyPatternTimingLink id="tl1">
                    <From>
                        <SequenceNumber>1</SequenceNumber>
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp1</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                    </From>
                        <To>
                        <SequenceNumber>2</SequenceNumber>
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp2</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                        </To>
                        <RouteLinkRef>rl1</RouteLinkRef>
                        <RunTime>PT5M</RunTime>
                        <Distance>1000</Distance>
                        </JourneyPatternTimingLink>
                        </JourneyPatternSection>
                    """,
            None,
            id="Missing required id attribute",
        ),
        pytest.param(
            """
            <JourneyPatternSection id="jps1">
                <JourneyPatternTimingLink id="tl1">
                    <From>
                        <SequenceNumber>1</SequenceNumber>
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp1</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                    </From>
                    <To>
                        <SequenceNumber>2</SequenceNumber>
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp2</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                    </To>
                    <RouteLinkRef>rl1</RouteLinkRef>
                    <Distance>1000</Distance>
                </JourneyPatternTimingLink>
            </JourneyPatternSection>
            """,
            None,
            id="JourneyPatternSection with invalid JourneyPatternTimingLink",
        ),
        pytest.param(
            """
            <JourneyPatternSection id="jps1">
            </JourneyPatternSection>
            """,
            None,
            id="No valid JourneyPatternTimingLinks",
        ),
    ],
)
def test_parse_journey_pattern_section(
    xml_string: str, expected_result: TXCJourneyPatternSection | None
) -> None:
    """
    JPS Parsing tests
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_journey_pattern_section(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <TransXChange>
            <JourneyPatternSections>
                <JourneyPatternSection id="jps1">
                    <JourneyPatternTimingLink id="tl1">
                    <From id="JPSU1">
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp1</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                        </From>
                        <To id="JPSU2">
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp2</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                        </To>
                        <RouteLinkRef>rl1</RouteLinkRef>
                        <RunTime>PT5M</RunTime>
                        <Distance>1000</Distance>
                    </JourneyPatternTimingLink>
                </JourneyPatternSection>
                <JourneyPatternSection id="jps2">
                    <JourneyPatternTimingLink id="tl2">
                        <From id="JPSU3">
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp2</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                        </From>
                        <To id="JPSU4">
                        <Activity>pickUpAndSetDown</Activity>
                        <StopPointRef>sp3</StopPointRef>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                        </To>
                        <RouteLinkRef>rl2</RouteLinkRef>
                        <RunTime>PT10M</RunTime>
                        <Distance>2000</Distance>
                    </JourneyPatternTimingLink>
                </JourneyPatternSection>
            </JourneyPatternSections>
            </TransXChange>
            """,
            [
                TXCJourneyPatternSection(
                    id="jps1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="tl1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                Activity="pickUpAndSetDown",
                                StopPointRef="sp1",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                Activity="pickUpAndSetDown",
                                StopPointRef="sp2",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="rl1",
                            RunTime="PT5M",
                            Distance="1000",
                        ),
                    ],
                ),
                TXCJourneyPatternSection(
                    id="jps2",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="tl2",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU3",
                                Activity="pickUpAndSetDown",
                                StopPointRef="sp2",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU4",
                                Activity="pickUpAndSetDown",
                                StopPointRef="sp3",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="rl2",
                            RunTime="PT10M",
                            Distance="2000",
                        ),
                    ],
                ),
            ],
            id="Valid",
        ),
        pytest.param(
            """
            <TransXChange>
                <JourneyPatternSections>
                    <JourneyPatternSection id="jps1">
                        <JourneyPatternTimingLink id="tl1">
                            <From id="JPSU1">
                            <Activity>pickUpAndSetDown</Activity>
                            <StopPointRef>sp1</StopPointRef>
                            <TimingStatus>principalTimingPoint</TimingStatus>
                            </From>
                            <To id="JPSU2">
                            <Activity>pickUpAndSetDown</Activity>
                            <StopPointRef>sp2</StopPointRef>
                            <TimingStatus>principalTimingPoint</TimingStatus>
                            </To>
                            <RouteLinkRef>rl1</RouteLinkRef>
                            <RunTime>PT5M</RunTime>
                            <Distance>1000</Distance>
                        </JourneyPatternTimingLink>
                    </JourneyPatternSection>
                    <JourneyPatternSection>
                        <JourneyPatternTimingLink id="tl2">
                            <From id="JPSU3">
                            <Activity>pickUpAndSetDown</Activity>
                            <StopPointRef>sp2</StopPointRef>
                            <TimingStatus>principalTimingPoint</TimingStatus>
                            </From>
                            <To id="JPSU4">
                            <Activity>pickUpAndSetDown</Activity>
                            <StopPointRef>sp3</StopPointRef>
                            <TimingStatus>principalTimingPoint</TimingStatus>
                            </To>
                            <RouteLinkRef>rl2</RouteLinkRef>
                            <RunTime>PT10M</RunTime>
                            <Distance>2000</Distance>
                        </JourneyPatternTimingLink>
                    </JourneyPatternSection>
                </JourneyPatternSections>
            </TransXChange>
            """,
            [
                TXCJourneyPatternSection(
                    id="jps1",
                    JourneyPatternTimingLink=[
                        TXCJourneyPatternTimingLink(
                            id="tl1",
                            From=TXCJourneyPatternStopUsage(
                                id="JPSU1",
                                Activity="pickUpAndSetDown",
                                StopPointRef="sp1",
                                TimingStatus="principalTimingPoint",
                            ),
                            To=TXCJourneyPatternStopUsage(
                                id="JPSU2",
                                Activity="pickUpAndSetDown",
                                StopPointRef="sp2",
                                TimingStatus="principalTimingPoint",
                            ),
                            RouteLinkRef="rl1",
                            RunTime="PT5M",
                            Distance="1000",
                        ),
                    ],
                ),
            ],
            id="One valid and one invalid JourneyPatternSection",
        ),
        pytest.param(
            """
            <TransXChange>
            <JourneyPatternSections>
            </JourneyPatternSections>
            </TransXChange>
            """,
            [],
            id="Empty JourneyPatternSections",
        ),
        pytest.param(
            """
            <TransXChange>
            </TransXChange>
            """,
            [],
            id="Missing JourneyPatternSections",
        ),
    ],
)
def test_parse_journey_pattern_sections(
    xml_string: str, expected_result: list[TXCJourneyPatternSection]
) -> None:
    """
    Journey Pattern Sections Parsing
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_journey_pattern_sections(xml_element)
    assert result == expected_result
