"""
Test Parsing StandardService in a TXC Service
"""

import pytest
from common_layer.txc.models import TXCJourneyPattern, TXCStandardService
from common_layer.txc.parser.services import parse_standard_service
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <StandardService>
                <Origin>Start Town</Origin>
                <Destination>End City</Destination>
                <JourneyPattern id="jp_1">
                    <DestinationDisplay>End City</DestinationDisplay>
                    <Direction>outbound</Direction>
                    <RouteRef>route_1</RouteRef>
                    <JourneyPatternSectionRefs>section_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
            """,
            TXCStandardService(
                Origin="Start Town",
                Destination="End City",
                JourneyPattern=[
                    TXCJourneyPattern(
                        id="jp_1",
                        DestinationDisplay="End City",
                        Direction="outbound",
                        RouteRef="route_1",
                        JourneyPatternSectionRefs=["section_1"],
                    )
                ],
            ),
            id="Standard service with journey pattern",
        ),
        pytest.param(
            """
            <StandardService>
                <Origin>Start Town</Origin>
                <Destination>End City</Destination>
            </StandardService>
            """,
            TXCStandardService(
                Origin="Start Town", Destination="End City", JourneyPattern=[]
            ),
            id="Minimal standard service",
        ),
    ],
)
def test_parse_standard_service(xml_string, expected_result):
    """Test parsing of StandardService section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_standard_service(xml_element)
    assert result == expected_result
