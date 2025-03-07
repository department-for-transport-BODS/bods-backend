"""
JourneyPatternStopUsage
"""

import pytest
from common_layer.xml.txc.models import TXCJourneyPatternStopUsage
from common_layer.xml.txc.parser.journey_pattern_sections import (
    parse_journey_pattern_stop_usage,
)
from lxml import etree


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
            <JourneyPatternStopUsage id="su1" SequenceNumber="5">
                <Activity>pickUpAndSetDown</Activity>
                <StopPointRef>sp1</StopPointRef>
                <TimingStatus>principalTimingPoint</TimingStatus>
            </JourneyPatternStopUsage>
            """,
            TXCJourneyPatternStopUsage(
                id="su1",
                Activity="pickUpAndSetDown",
                StopPointRef="sp1",
                TimingStatus="principalTimingPoint",
                SequenceNumber="5",
            ),
            id="Sequence number",
        ),
        pytest.param(
            """
            <JourneyPatternStopUsage id="su1" SequenceNumber="5">
                <Activity>pickUpAndSetDown</Activity>
                <StopPointRef>sp1</StopPointRef>
            </JourneyPatternStopUsage>
            """,
            TXCJourneyPatternStopUsage(
                id="su1",
                Activity="pickUpAndSetDown",
                StopPointRef="sp1",
                TimingStatus=None,
                SequenceNumber="5",
            ),
            id="Missing TimingStatus number",
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
def test_parse_journey_pattern_stop_usage(
    xml_string: str, expected_result: TXCJourneyPatternStopUsage | None
):
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
                <DynamicDestinationDisplay>Destination</DynamicDestinationDisplay>
                <Notes>Test notes</Notes>
                <StopPointRef>sp1</StopPointRef>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <FareStageNumber>1</FareStageNumber>
                <FareStage>true</FareStage>
            </JourneyPatternStopUsage>
            """,
            id="JourneyPatternStopUsage missing Activity defaults to pickUpAndSetDown",
        ),
    ],
)
def test_parse_journey_pattern_stop_usage_defaults(xml_string: str):
    """
    Scenarios where it should return None
    """
    xml_element = etree.fromstring(xml_string)
    parsed = parse_journey_pattern_stop_usage(xml_element)
    if parsed is not None:
        assert parsed.Activity == "pickUpAndSetDown"
