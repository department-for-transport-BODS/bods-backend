"""
Test Parsing a Tariff
"""

import pytest
from common_layer.xml.netex.models.fare_frame.netex_sales_offer_package import (
    SalesOfferPackage,
)
from common_layer.xml.netex.parser.fare_frame.netex_fare_sales_offer_package import (
    parse_sales_offer_package,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <SalesOfferPackage id="Trip@ADRTN-SOP@Onboard" version="1.0">
              <Name>Onboard</Name>
              <Description>Purchasable on board the bus, with cash or contactless card, as a paper
                ticket.</Description>
              <distributionAssignments>
                <DistributionAssignment id="Trip@ADRTN-SOP@Onboard@OnBoard" version="any" order="1">
                  <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
                  <DistributionChannelType>onBoard</DistributionChannelType>
                  <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
                </DistributionAssignment>
              </distributionAssignments>
              <salesOfferPackageElements>
                <SalesOfferPackageElement id="Trip@ADRTN-SOP@Onboard@printed_ticket" version="1.0" order="1">
                  <TypeOfTravelDocumentRef version="fxc:v1.0" ref="fxc:printed_ticket" />
                  <PreassignedFareProductRef version="1.0" ref="Trip@ADRTN" />
                </SalesOfferPackageElement>
              </salesOfferPackageElements>
            </SalesOfferPackage>
            """,
            SalesOfferPackage(id="Trip@ADRTN-SOP@Onboard", version="1.0"),
            id="Basic sales offer package",
        ),
    ],
)
def test_parse_sales_offer_package(xml_str: str, expected: SalesOfferPackage) -> None:
    """Test parsing of sales offer package."""
    elem = parse_xml_str_as_netex(xml_str)

    result = parse_sales_offer_package(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <SalesOfferPackage id="Trip@ADRTN-SOP@Onboard">
              <Name>Onboard</Name>
              <Description>Purchasable on board the bus, with cash or contactless card, as a paper
                ticket.</Description>
              <distributionAssignments>
                <DistributionAssignment id="Trip@ADRTN-SOP@Onboard@OnBoard" version="any" order="1">
                  <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
                  <DistributionChannelType>onBoard</DistributionChannelType>
                  <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
                </DistributionAssignment>
              </distributionAssignments>
              <salesOfferPackageElements>
                <SalesOfferPackageElement id="Trip@ADRTN-SOP@Onboard@printed_ticket" version="1.0" order="1">
                  <TypeOfTravelDocumentRef version="fxc:v1.0" ref="fxc:printed_ticket" />
                  <PreassignedFareProductRef version="1.0" ref="Trip@ADRTN" />
                </SalesOfferPackageElement>
              </salesOfferPackageElements>
            </SalesOfferPackage>
            """,
            SalesOfferPackage(id="Trip@ADRTN-SOP@Onboard", version="1.0"),
            id="Basic sales offer package",
        ),
    ],
)
def test_parse_sales_offer_package_with_missing_attributes(
    xml_str: str, expected: SalesOfferPackage
) -> None:
    """Test parsing of sales offer package."""
    elem = parse_xml_str_as_netex(xml_str)

    with pytest.raises(
        ValueError, match="Missing required id or version in sales offer package"
    ):
        result = parse_sales_offer_package(elem)
        assert_model_equal(result, expected)
