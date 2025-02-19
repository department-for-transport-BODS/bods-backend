"""
FareFrame Pricing parameter set
"""

import pytest
from common_layer.xml.netex.models import MultilingualString, PriceUnit
from common_layer.xml.netex.models.fare_frame.netex_frame_fare import (
    PricingParameterSet,
)
from common_layer.xml.netex.parser.fare_frame.netex_pricing_parameter_set import (
    parse_price_unit,
    parse_pricing_parameter_set,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <PriceUnit id="fxc:GBP" version="fxc:v1.0">
                <Name>Pound Sterling</Name>
                <PrivateCode>£</PrivateCode>
                <Precision>2</Precision>
            </PriceUnit>
            """,
            PriceUnit(
                id="fxc:GBP",
                version="fxc:v1.0",
                Name=MultilingualString(value="Pound Sterling"),
                PrivateCode="£",
                Precision=2,
            ),
            id="Basic price unit",
        ),
    ],
)
def test_parse_price_unit(xml_str: str, expected: PriceUnit) -> None:
    """Test parsing of price unit with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_price_unit(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <PricingParameterSet id="fxc:Common_Resources" version="fxc:v1.0">
                <priceUnits>
                    <PriceUnit id="fxc:GBP" version="fxc:v1.0">
                        <Name>Pound Sterling</Name>
                        <PrivateCode>£</PrivateCode>
                        <Precision>2</Precision>
                    </PriceUnit>
                    <PriceUnit id="fxc:EUR" version="fxc:v1.0">
                        <Name>Euro</Name>
                        <PrivateCode>€</PrivateCode>
                        <Precision>2</Precision>
                    </PriceUnit>
                </priceUnits>
            </PricingParameterSet>
            """,
            PricingParameterSet(
                id="fxc:Common_Resources",
                version="fxc:v1.0",
                priceUnits=[
                    PriceUnit(
                        id="fxc:GBP",
                        version="fxc:v1.0",
                        Name=MultilingualString(value="Pound Sterling"),
                        PrivateCode="£",
                        Precision=2,
                    ),
                    PriceUnit(
                        id="fxc:EUR",
                        version="fxc:v1.0",
                        Name=MultilingualString(value="Euro"),
                        PrivateCode="€",
                        Precision=2,
                    ),
                ],
            ),
            id="Basic pricing parameter set",
        ),
    ],
)
def test_parse_pricing_parameter_set(
    xml_str: str, expected: PricingParameterSet
) -> None:
    """Test parsing of pricing parameter set with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_pricing_parameter_set(elem)
    assert_model_equal(result, expected)


def test_parse_price_unit_missing_attributes() -> None:
    """Test parsing of price unit with missing required attributes."""
    xml_str = """
        <PriceUnit>
            <Name>Test Unit</Name>
            <PrivateCode>£</PrivateCode>
            <Precision>2</Precision>
        </PriceUnit>
        """
    elem = parse_xml_str_as_netex(xml_str)

    with pytest.raises(ValueError, match="Missing required id or version in PriceUnit"):
        parse_price_unit(elem)


def test_parse_pricing_parameter_set_empty() -> None:
    """Test parsing of pricing parameter set with no price units."""
    xml_str = """
        <PricingParameterSet id="test" version="1.0">
            <priceUnits>
            </priceUnits>
        </PricingParameterSet>
        """
    elem = parse_xml_str_as_netex(xml_str)

    with pytest.raises(
        ValueError, match="PricingParameterSet must contain at least one PriceUnit"
    ):
        parse_pricing_parameter_set(elem)
