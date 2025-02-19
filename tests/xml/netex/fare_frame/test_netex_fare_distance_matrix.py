"""
Test parsing distance matrix
"""

import pytest
from common_layer.xml.netex.models import DistanceMatrixElement, VersionedRef
from common_layer.xml.netex.parser import parse_distance_matrix_element

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


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
                priceGroups=[
                    VersionedRef(
                        version="1.0",
                        ref="price_band_3.0",
                    ),
                ],
                StartTariffZoneRef=VersionedRef(
                    version="1.0",
                    ref="fs@1501",
                ),
                EndTariffZoneRef=VersionedRef(
                    version="1.0",
                    ref="fs@1516",
                ),
            ),
            id="Basic distance matrix element",
        ),
        pytest.param(
            """
            <DistanceMatrixElement id="1501+1516" version="1.0">
                <StartTariffZoneRef version="1.0" ref="fs@1501" />
                <EndTariffZoneRef version="1.0" ref="fs@1516" />
            </DistanceMatrixElement>
            """,
            DistanceMatrixElement(
                id="1501+1516",
                version="1.0",
                priceGroups=[],
                StartTariffZoneRef=VersionedRef(
                    version="1.0",
                    ref="fs@1501",
                ),
                EndTariffZoneRef=VersionedRef(
                    version="1.0",
                    ref="fs@1516",
                ),
            ),
            id="Distance matrix element without price groups",
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
                    VersionedRef(
                        version="1.0",
                        ref="price_band_3.0",
                    ),
                    VersionedRef(
                        version="1.0",
                        ref="price_band_4.0",
                    ),
                ],
                StartTariffZoneRef=VersionedRef(
                    version="1.0",
                    ref="fs@1501",
                ),
                EndTariffZoneRef=VersionedRef(
                    version="1.0",
                    ref="fs@1516",
                ),
            ),
            id="Distance matrix element with multiple price groups",
        ),
    ],
)
def test_parse_distance_matrix_element(
    xml_str: str, expected: DistanceMatrixElement
) -> None:
    """Test parsing of distance matrix element with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_distance_matrix_element(elem)
    assert_model_equal(result, expected)
