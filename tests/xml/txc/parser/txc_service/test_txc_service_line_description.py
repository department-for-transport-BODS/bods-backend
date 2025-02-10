"""
Test Parsing a TXC Service Line Description
"""

import pytest
from common_layer.xml.txc.models import TXCLineDescription
from common_layer.xml.txc.parser.services import parse_line_description
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <OutboundDescription>
                <Origin>Start</Origin>
                <Destination>End</Destination>
                <Description>Via Center</Description>
            </OutboundDescription>
            """,
            TXCLineDescription(
                Origin="Start", Destination="End", Description="Via Center"
            ),
            id="Complete outbound description",
        ),
        pytest.param(
            """
            <InboundDescription>
                <Origin>End</Origin>
                <Destination>Start</Destination>
                <Description>Return via Center</Description>
            </InboundDescription>
            """,
            TXCLineDescription(
                Origin="End", Destination="Start", Description="Return via Center"
            ),
            id="Complete inbound description",
        ),
        pytest.param(
            """
            <OutboundDescription>
                <Origin>Knighton Saffron Crossroads</Origin>
                <Destination>Knighton Weldon Road</Destination>
                <Vias>
                    <Via>Roehampton Drive</Via>
                </Vias>
                <Description>Knighton Saffron Crossroads to Knighton Weldon Road</Description>
            </OutboundDescription>
            """,
            TXCLineDescription(
                Origin="Knighton Saffron Crossroads",
                Destination="Knighton Weldon Road",
                Description="Knighton Saffron Crossroads to Knighton Weldon Road",
                Vias=["Roehampton Drive"],
            ),
            id="Description with 1 Via",
        ),
        pytest.param(
            """
            <OutboundDescription>
                <Origin>London Victoria</Origin>
                <Destination>Edinburgh</Destination>
                <Vias>
                    <Via>Manchester</Via>
                    <Via>Leeds</Via>
                </Vias>
                <Description>A Journey</Description>
            </OutboundDescription>
            """,
            TXCLineDescription(
                Origin="London Victoria",
                Destination="Edinburgh",
                Description="A Journey",
                Vias=["Manchester", "Leeds"],
            ),
            id="Description with 2 Vias",
        ),
        pytest.param(
            """
            <OutboundDescription>
                <Description>Direct service</Description>
            </OutboundDescription>
            """,
            TXCLineDescription(Description="Direct service"),
            id="Minimal description with only required field",
        ),
    ],
)
def test_parse_line_description(xml_string, expected_result):
    """Test parsing of LineDescription section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_line_description(xml_element)
    assert result == expected_result
