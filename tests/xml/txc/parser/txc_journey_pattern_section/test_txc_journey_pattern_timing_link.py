"""
Test JourneyPatternSection JourneyPatternTimingLink
"""

import pytest
from common_layer.xml.txc.models import (
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
)
from common_layer.xml.txc.parser.journey_pattern_sections import (
    parse_journey_pattern_timing_link,
)
from lxml import etree


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
