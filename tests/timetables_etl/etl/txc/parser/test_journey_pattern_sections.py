"""
Test Parsing Funtions for xml of journey pattern sections
"""

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.models.txc_journey_pattern import (
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
)
from timetables_etl.etl.app.txc.parser.journey_pattern_sections import (
    parse_journey_pattern_section,
    parse_journey_pattern_sections,
    parse_journey_pattern_stop_usage,
    parse_journey_pattern_timing_link,
)


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <JourneyPatternStopUsage id="su1">
                <WaitTime>PT1M</WaitTime>
                <Activity>pickUpAndSetDown</Activity>
                <DynamicDestinationDisplay>Destination</DynamicDestinationDisplay>
                <Notes>Test notes</Notes>
                <StopPointRef>sp1</StopPointRef>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <FareStageNumber>1</FareStageNumber>
                <FareStage>true</FareStage>
            </JourneyPatternStopUsage>
            """,
            TXCJourneyPatternStopUsage(
                id="su1",
                WaitTime="PT1M",
                Activity="pickUpAndSetDown",
                DynamicDestinationDisplay="Destination",
                Notes="Test notes",
                StopPointRef="sp1",
                TimingStatus="principalTimingPoint",
                FareStageNumber=1,
                FareStage=True,
            ),
            id="Valid JourneyPatternStopUsage",
        ),
        pytest.param(
            """
            <JourneyPatternStopUsage id="su1">
                <SequenceNumber>1</SequenceNumber>
                <WaitTime>PT1M</WaitTime>
                <Activity>pickUpAndSetDown</Activity>
                <DynamicDestinationDisplay>Destination</DynamicDestinationDisplay>
                <Notes>Test notes</Notes>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <FareStageNumber>1</FareStageNumber>
                <FareStage>true</FareStage>
            </JourneyPatternStopUsage>
            """,
            None,
            id="JourneyPatternStopUsage missing required StopPointRef",
        ),
    ],
)
def test_parse_journey_pattern_stop_usage(xml_string, expected_result):
    """
    Parse JPTS
    TODO: Parse Stop Usage
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_journey_pattern_stop_usage(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string",
    [
        pytest.param(
            """
            <JourneyPatternStopUsage id="su1">
                <SequenceNumber>1</SequenceNumber>
                <WaitTime>PT1M</WaitTime>
                <Activity>pickUpAndSetDown</Activity>
                <DynamicDestinationDisplay>Destination</DynamicDestinationDisplay>
                <Notes>Test notes</Notes>
                <StopPointRef>sp1</StopPointRef>
                <FareStageNumber>1</FareStageNumber>
                <FareStage>true</FareStage>
            </JourneyPatternStopUsage>
            """,
            id="JourneyPatternStopUsage missing required TimingStatus",
        ),
        pytest.param(
            """
            <JourneyPatternStopUsage id="su1">
                <SequenceNumber>1</SequenceNumber>
                <WaitTime>PT1M</WaitTime>
                <DynamicDestinationDisplay>Destination</DynamicDestinationDisplay>
                <Notes>Test notes</Notes>
                <StopPointRef>sp1</StopPointRef>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <FareStageNumber>1</FareStageNumber>
                <FareStage>true</FareStage>
            </JourneyPatternStopUsage>
            """,
            id="JourneyPatternStopUsage missing required Activity",
        ),
    ],
)
def test_parse_journey_pattern_stop_usage_except(xml_string):
    """
    Default setting test
    """
    xml_element = etree.fromstring(xml_string)
    parsed = parse_journey_pattern_stop_usage(xml_element)
    if parsed is not None:
        assert parsed.Activity == "pickUpAndSetDown"
        assert parsed.TimingStatus == "principalTimingPoint"


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
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
            """,
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
            id="Valid",
        ),
        pytest.param(
            """
            <JourneyPatternTimingLink>
                <From>
                    <Activity>pickUpAndSetDown</Activity>
                    <StopPointRef>sp1</StopPointRef>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                </From>
                <To>
                    <Activity>pickUpAndSetDown</Activity>
                    <StopPointRef>sp2</StopPointRef>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                </To>
                <RouteLinkRef>rl1</RouteLinkRef>
                <RunTime>PT5M</RunTime>
                <Distance>1000</Distance>
            </JourneyPatternTimingLink>
            """,
            None,
            id="Missing required id attribute",
        ),
        pytest.param(
            """
            <JourneyPatternTimingLink id="tl1">
                <To>
                    <Activity>pickUpAndSetDown</Activity>
                    <StopPointRef>sp2</StopPointRef>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                </To>
                <RouteLinkRef>rl1</RouteLinkRef>
                <RunTime>PT5M</RunTime>
                <Distance>1000</Distance>
            </JourneyPatternTimingLink>
            """,
            None,
            id="Missing required From element",
        ),
        pytest.param(
            """
            <JourneyPatternTimingLink id="tl1">
                <From>
                    <Activity>pickUpAndSetDown</Activity>
                    <StopPointRef>sp1</StopPointRef>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                </From>
                <RouteLinkRef>rl1</RouteLinkRef>
                <RunTime>PT5M</RunTime>
                <Distance>1000</Distance>
            </JourneyPatternTimingLink>
            """,
            None,
            id="Missing required To element",
        ),
        pytest.param(
            """
            <JourneyPatternTimingLink id="tl1">
                <From>
                    <Activity>pickUpAndSetDown</Activity>
                    <StopPointRef>sp1</StopPointRef>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                </From>
                <To>
                    <Activity>pickUpAndSetDown</Activity>
                    <StopPointRef>sp2</StopPointRef>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                </To>
                <RunTime>PT5M</RunTime>
                <Distance>1000</Distance>
            </JourneyPatternTimingLink>
            """,
            None,
            id="Missing required RouteLinkRef",
        ),
        pytest.param(
            """
            <JourneyPatternTimingLink id="tl1">
                <From>
                    <Activity>pickUpAndSetDown</Activity>
                    <StopPointRef>sp1</StopPointRef>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                </From>
                <To>
                    <Activity>pickUpAndSetDown</Activity>
                    <StopPointRef>sp2</StopPointRef>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                </To>
                <RouteLinkRef>rl1</RouteLinkRef>
                <Distance>1000</Distance>
            </JourneyPatternTimingLink>
            """,
            None,
            id="Missing required RunTime",
        ),
    ],
)
def test_parse_journey_pattern_timing_link(xml_string, expected_result):
    """
    Timing Link Parsing
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_journey_pattern_timing_link(xml_element)
    assert result == expected_result


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
def test_parse_journey_pattern_section(xml_string, expected_result):
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
def test_parse_journey_pattern_sections(xml_string, expected_result):
    """
    Journey Pattern Sections Parsing
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_journey_pattern_sections(xml_element)
    assert result == expected_result
