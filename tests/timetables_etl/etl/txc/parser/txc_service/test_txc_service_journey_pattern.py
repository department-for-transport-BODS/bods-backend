"""
Test Parsing JourneyPattern in a TXC Service 
"""

import pytest
from common_layer.txc.models import TXCJourneyPattern
from common_layer.txc.parser.services import parse_journey_pattern
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <JourneyPattern id="jp_1">
                <PrivateCode>PC123</PrivateCode>
                <DestinationDisplay>City Center</DestinationDisplay>
                <Direction>outbound</Direction>
                <RouteRef>route_1</RouteRef>
                <JourneyPatternSectionRefs>section_1</JourneyPatternSectionRefs>
                <Description>Main Route</Description>
                <LayoverPoint>stop_1</LayoverPoint>
                <OperatorRef>op_1</OperatorRef>
            </JourneyPattern>
            """,
            TXCJourneyPattern(
                id="jp_1",
                PrivateCode="PC123",
                DestinationDisplay="City Center",
                Direction="outbound",
                RouteRef="route_1",
                JourneyPatternSectionRefs=["section_1"],
                Description="Main Route",
                LayoverPoint="stop_1",
                OperatorRef="op_1",
            ),
            id="Full journey pattern",
        ),
        pytest.param(
            """
            <JourneyPattern id="jp_2">
                <DestinationDisplay>City Center</DestinationDisplay>
                <Direction>inbound</Direction>
                <RouteRef>route_2</RouteRef>
                <JourneyPatternSectionRefs>section_1</JourneyPatternSectionRefs>
            </JourneyPattern>
            """,
            TXCJourneyPattern(
                id="jp_2",
                DestinationDisplay="City Center",
                Direction="inbound",
                RouteRef="route_2",
                JourneyPatternSectionRefs=["section_1"],
            ),
            id="Minimal journey pattern",
        ),
    ],
)
def test_parse_journey_pattern(xml_string, expected_result):
    """Test parsing of JourneyPattern section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_journey_pattern(xml_element)
    assert result == expected_result
