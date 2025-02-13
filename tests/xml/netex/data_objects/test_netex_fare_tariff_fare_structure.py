"""
Test FareStructure
"""

import pytest
from common_layer.xml.netex.models import DistanceMatrixElement, VersionedRef
from common_layer.xml.netex.parser import parse_distance_matrix_element
from lxml.etree import fromstring

from tests.xml.conftest import assert_model_equal


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <DistanceMatrixElement id="1501+1516" version="1.0">
                <priceGroups>
                    <PriceGroupRef version="1.0" ref="price_band_3.0" />
                </priceGroups>
                <StartTariffZoneRef version="1.0" ref="fs@1501" />
                <EndTariffZoneRef version="1.0" ref="fs@1516" />
            </DistanceMatrixElement>
            """,
            DistanceMatrixElement(
                id="1501+1516",
                version="1.0",
                priceGroups=[VersionedRef(version="1.0", ref="price_band_3.0")],
                StartTariffZoneRef=VersionedRef(version="1.0", ref="fs@1501"),
                EndTariffZoneRef=VersionedRef(version="1.0", ref="fs@1516"),
            ),
            id="Basic distance matrix element",
        ),
        pytest.param(
            """
            <DistanceMatrixElement id="1501+1516" version="1.0">
                <priceGroups>
                    <PriceGroupRef version="1.0" ref="price_band_3.0" />
                    <PriceGroupRef version="1.0" ref="price_band_4.0" />
                </priceGroups>
                <StartTariffZoneRef version="1.0" ref="fs@1501" />
                <EndTariffZoneRef version="1.0" ref="fs@1516" />
            </DistanceMatrixElement>
            """,
            DistanceMatrixElement(
                id="1501+1516",
                version="1.0",
                priceGroups=[
                    VersionedRef(version="1.0", ref="price_band_3.0"),
                    VersionedRef(version="1.0", ref="price_band_4.0"),
                ],
                StartTariffZoneRef=VersionedRef(version="1.0", ref="fs@1501"),
                EndTariffZoneRef=VersionedRef(version="1.0", ref="fs@1516"),
            ),
            id="Distance matrix element with multiple price groups",
        ),
        pytest.param(
            """
            <DistanceMatrixElement id="1501+1516" version="1.0">
                <priceGroups>
                    <PriceGroupRef version="1.0" ref="price_band_3.0" />
                </priceGroups>
                <StartTariffZoneRef version="1.0" ref="fs@1501" />
                <EndTariffZoneRef version="1.0" ref="fs@1516" />
                <UnknownTag>Some content</UnknownTag>
            </DistanceMatrixElement>
            """,
            DistanceMatrixElement(
                id="1501+1516",
                version="1.0",
                priceGroups=[VersionedRef(version="1.0", ref="price_band_3.0")],
                StartTariffZoneRef=VersionedRef(version="1.0", ref="fs@1501"),
                EndTariffZoneRef=VersionedRef(version="1.0", ref="fs@1516"),
            ),
            id="Distance matrix element with unknown tag",
        ),
        pytest.param(
            """
            <DistanceMatrixElement id="1501+1516" version="1.0">
                <StartTariffZoneRef version="1.0" ref="fs@1501" />
                <EndTariffZoneRef version="1.0" ref="fs@1516" />
            </DistanceMatrixElement>
            """,
            None,
            id="Distance matrix element missing price groups",
            marks=pytest.mark.xfail(raises=ValueError, strict=True),
        ),
    ],
)
def test_parse_distance_matrix_element(
    xml_str: str, expected: DistanceMatrixElement
) -> None:
    """Test parsing of distance matrix element with various inputs."""
    elem = fromstring(xml_str.strip())
    result = parse_distance_matrix_element(elem)
    assert_model_equal(result, expected)
