"""
PriceGroups Parsing
"""

import pytest
from common_layer.xml.netex.models import VersionedRef
from common_layer.xml.netex.parser import parse_price_groups

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <priceGroups>
                <PriceGroupRef version="1.0" ref="price_band_3.0" />
            </priceGroups>
            """,
            [
                VersionedRef(
                    version="1.0",
                    ref="price_band_3.0",
                ),
            ],
            id="Single price group ref",
        ),
        pytest.param(
            """
            <priceGroups>
                <PriceGroupRef version="1.0" ref="price_band_3.0" />
                <PriceGroupRef version="1.0" ref="price_band_4.0" />
            </priceGroups>
            """,
            [
                VersionedRef(
                    version="1.0",
                    ref="price_band_3.0",
                ),
                VersionedRef(
                    version="1.0",
                    ref="price_band_4.0",
                ),
            ],
            id="Multiple price group refs",
        ),
        pytest.param(
            """
            <priceGroups>
            </priceGroups>
            """,
            [],
            id="Empty price groups",
        ),
    ],
)
def test_parse_price_groups_refs(xml_str: str, expected: list[VersionedRef]) -> None:
    """Test parsing of price group refs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_price_groups(elem)

    for result_ref, expected_ref in zip(result, expected):
        assert_model_equal(result_ref, expected_ref)
