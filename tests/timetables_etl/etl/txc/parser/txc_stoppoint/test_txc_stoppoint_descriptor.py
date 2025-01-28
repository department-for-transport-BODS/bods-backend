"""
Test Parsing TXC StopPoint Descriptor
"""

import pytest
from common_layer.txc.models import DescriptorStructure
from common_layer.txc.parser.stop_points import parse_descriptor_structure
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "descriptor_xml_str, expected_result",
    [
        pytest.param(
            """
            <Descriptor>
                <CommonName>Dublin (George's Quay) Stop 135141</CommonName>
                <ShortCommonName>Dublin Stop</ShortCommonName>
                <Landmark>George's Quay</Landmark>
                <Street>Tara St</Street>
                <Crossing>George's Quay</Crossing>
                <Indicator>Stop 135141</Indicator>
            </Descriptor>
            """,
            DescriptorStructure(
                CommonName="Dublin (George's Quay) Stop 135141",
                ShortCommonName="Dublin Stop",
                Landmark="George's Quay",
                Street="Tara St",
                Crossing="George's Quay",
                Indicator="Stop 135141",
            ),
            id="Valid Descriptor Structure",
        ),
        pytest.param(
            """
            <Descriptor>
                <ShortCommonName>Dublin Stop</ShortCommonName>
                <Landmark>George's Quay</Landmark>
                <Street>Tara St</Street>
                <Crossing>George's Quay</Crossing>
                <Indicator>Stop 135141</Indicator>
            </Descriptor>
            """,
            None,
            id="Missing CommonName",
        ),
    ],
)
def test_parse_descriptor_structure(descriptor_xml_str, expected_result):
    """
    Parse Descriptor
    """
    descriptor_xml = fromstring(descriptor_xml_str)
    assert parse_descriptor_structure(descriptor_xml) == expected_result
