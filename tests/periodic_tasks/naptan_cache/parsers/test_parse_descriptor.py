"""
Test Descriptor Parsing
"""

import pytest
from lxml import etree

from periodic_tasks.naptan_cache.app.data_loader.parsers.parser_descriptor import (
    parse_descriptor,
)
from tests.periodic_tasks.naptan_cache.parsers.common import (
    create_stop_point,
    parse_xml_to_stop_point,
)


@pytest.mark.parametrize(
    ("xml_input", "expected"),
    [
        pytest.param(
            create_stop_point(
                """
                <Descriptor>
                    <CommonName>Temple Meads Stn</CommonName>
                    <ShortCommonName>Temple Meads Stn</ShortCommonName>
                    <Street>Redcliffe Way</Street>
                    <Indicator>T3</Indicator>
                </Descriptor>
            """
            ),
            {
                "CommonName": "Temple Meads Stn",
                "ShortCommonName": "Temple Meads Stn",
                "Street": "Redcliffe Way",
                "Landmark": None,
                "Indicator": "T3",
            },
            id="CompleteDescriptorData",
        ),
        pytest.param(
            create_stop_point(
                """
                <Descriptor>
                    <CommonName>Temple Meads Stn</CommonName>
                    <Street>Redcliffe Way</Street>
                </Descriptor>
            """
            ),
            {
                "CommonName": "Temple Meads Stn",
                "ShortCommonName": None,
                "Street": "Redcliffe Way",
                "Landmark": None,
                "Indicator": None,
            },
            id="PartialDescriptorData",
        ),
        pytest.param(
            create_stop_point(
                """
                <Descriptor>
                    <CommonName></CommonName>
                    <Street></Street>
                </Descriptor>
            """
            ),
            {
                "CommonName": None,
                "ShortCommonName": None,
                "Street": None,
                "Landmark": None,
                "Indicator": None,
            },
            id="EmptyDescriptorElements",
        ),
        pytest.param(
            create_stop_point("<Descriptor></Descriptor>"),
            {
                "CommonName": None,
                "ShortCommonName": None,
                "Street": None,
                "Landmark": None,
                "Indicator": None,
            },
            id="EmptyDescriptor",
        ),
        pytest.param(
            create_stop_point(""),
            {
                "CommonName": None,
                "ShortCommonName": None,
                "Street": None,
                "Landmark": None,
                "Indicator": None,
            },
            id="NoDescriptor",
        ),
    ],
)
def test_parse_descriptor(xml_input: str, expected: dict[str, str | None]) -> None:
    """
    Test parse_descriptor function with various input scenarios.

    """
    stop_point: etree._Element = parse_xml_to_stop_point(xml_input)
    result: dict[str, str | None] = parse_descriptor(stop_point)
    assert result == expected
