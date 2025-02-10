"""
Test Parsing Line Section of a TXC Service
"""

import pytest
from common_layer.xml.txc.models import TXCLine, TXCLineDescription
from common_layer.xml.txc.parser.services import parse_line
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <Line id="line_1">
                <LineName>42</LineName>
                <MarketingName>Express</MarketingName>
                <OutboundDescription>
                    <Origin>Start</Origin>
                    <Destination>End</Destination>
                    <Description>Via Center</Description>
                </OutboundDescription>
                <InboundDescription>
                    <Origin>End</Origin>
                    <Destination>Start</Destination>
                    <Description>Via Center Return</Description>
                </InboundDescription>
            </Line>
            """,
            TXCLine(
                id="line_1",
                LineName="42",
                MarketingName="Express",
                OutboundDescription=TXCLineDescription(
                    Origin="Start", Destination="End", Description="Via Center"
                ),
                InboundDescription=TXCLineDescription(
                    Origin="End", Destination="Start", Description="Via Center Return"
                ),
            ),
            id="Complete line",
        ),
        pytest.param(
            """
            <Line id="line_2">
                <LineName>43</LineName>
            </Line>
            """,
            TXCLine(id="line_2", LineName="43"),
            id="Minimal line",
        ),
    ],
)
def test_parse_line(xml_string, expected_result):
    """Test parsing of Line section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_line(xml_element)
    assert result == expected_result
