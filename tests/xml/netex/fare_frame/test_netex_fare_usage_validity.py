"""
UsageValidatityPeriod Parsing Tests
"""

import pytest
from common_layer.xml.netex.models import UsageValidityPeriod
from common_layer.xml.netex.parser import parse_usage_validity_period

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
           <UsageValidityPeriod version="1.0" id="Trip@AdultSingle@back@frequency">
               <UsageTrigger>purchase</UsageTrigger>
               <UsageEnd>standardDuration</UsageEnd>
               <ActivationMeans>noneRequired</ActivationMeans>
           </UsageValidityPeriod>
           """,
            UsageValidityPeriod(
                id="Trip@AdultSingle@back@frequency",
                version="1.0",
                UsageTrigger="purchase",
                UsageEnd="standardDuration",
                ActivationMeans="noneRequired",
            ),
            id="Basic usage validity period",
        ),
        pytest.param(
            """
           <UsageValidityPeriod version="1.0" id="Trip@AdultSingle@back@frequency">
               <UsageTrigger>startOutboundRide</UsageTrigger>
               <UsageEnd>endOfFarePeriod</UsageEnd>
               <ActivationMeans>checkIn</ActivationMeans>
               <UnknownTag>some value</UnknownTag>
           </UsageValidityPeriod>
           """,
            UsageValidityPeriod(
                id="Trip@AdultSingle@back@frequency",
                version="1.0",
                UsageTrigger="startOutboundRide",
                UsageEnd="endOfFarePeriod",
                ActivationMeans="checkIn",
            ),
            id="Usage validity period with unknown tag",
        ),
    ],
)
def test_parse_usage_validity_period(
    xml_str: str, expected: UsageValidityPeriod
) -> None:
    """Test parsing of usage validity period with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_usage_validity_period(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str",
    [
        pytest.param(
            """
           <UsageValidityPeriod version="1.0" >
               <UsageTrigger>purchase</UsageTrigger>
               <UsageEnd>standardDuration</UsageEnd>
               <ActivationMeans>noneRequired</ActivationMeans>
           </UsageValidityPeriod>
           """,
            id="Missing ID",
        ),
        pytest.param(
            """
        <UsageValidityPeriod  id="Trip@AdultSingle@back@frequency">
            <UsageTrigger>purchase</UsageTrigger>
            <ActivationMeans>noneRequired</ActivationMeans>
        </UsageValidityPeriod>
           """,
            id="Missing version",
        ),
    ],
)
def test_parse_usage_validity_period_missing_fields(xml_str: str) -> None:
    """Test parsing of usage validity period with missing required fields."""
    xml_str = """
       <UsageValidityPeriod  id="Trip@AdultSingle@back@frequency">
           <UsageTrigger>purchase</UsageTrigger>
           <ActivationMeans>noneRequired</ActivationMeans>
       </UsageValidityPeriod>
       """
    elem = parse_xml_str_as_netex(xml_str)

    with pytest.raises(
        ValueError,
    ):
        parse_usage_validity_period(elem)
