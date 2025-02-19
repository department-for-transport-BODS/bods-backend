"""
Test Parsing a Tariff
"""

from datetime import datetime

import pytest
from common_layer.xml.netex.models import (
    DistanceMatrixElement,
    FareStructureElement,
    FromToDate,
    MultilingualString,
    Tariff,
    VersionedRef,
)
from common_layer.xml.netex.parser import parse_tariff

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <Tariff id="Tariff@AdultSingle@Line_BRTB:PC0003375:3:15" version="1.0">
                <validityConditions>
                    <ValidBetween>
                        <FromDate>2025-02-05T00:00:00</FromDate>
                        <ToDate>2125-02-05T00:00:00</ToDate>
                    </ValidBetween>
                </validityConditions>
                <Name>Trentbarton / Kinchbus 15 Inbound - Adult Single fares</Name>
                <OperatorRef version="1.0" ref="noc:BRTB" />
                <LineRef ref="BRTB:PC0003375:3:15" version="1.0" />
                <TypeOfTariffRef version="fxc:v1.0" ref="fxc:point_to_point" />
                <TariffBasis>pointToPoint</TariffBasis>
                <fareStructureElements>
                    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
                        <Name>O/D pairs for Line 15 Inbound</Name>
                        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
                        <distanceMatrixElements>
                            <DistanceMatrixElement id="1501+1516" version="1.0">
                                <priceGroups>
                                    <PriceGroupRef version="1.0" ref="price_band_3.0" />
                                </priceGroups>
                                <StartTariffZoneRef version="1.0" ref="fs@1501" />
                                <EndTariffZoneRef version="1.0" ref="fs@1516" />
                            </DistanceMatrixElement>
                        </distanceMatrixElements>
                    </FareStructureElement>
                </fareStructureElements>
            </Tariff>
            """,
            Tariff(
                id="Tariff@AdultSingle@Line_BRTB:PC0003375:3:15",
                version="1.0",
                validityConditions=[
                    FromToDate(
                        FromDate=datetime(2025, 2, 5, 0, 0),
                        ToDate=datetime(2125, 2, 5, 0, 0),
                    )
                ],
                Name=MultilingualString(
                    value="Trentbarton / Kinchbus 15 Inbound - Adult Single fares",
                    lang=None,
                    textIdType=None,
                ),
                OperatorRef=VersionedRef(version="1.0", ref="noc:BRTB"),
                LineRef=VersionedRef(version="1.0", ref="BRTB:PC0003375:3:15"),
                TypeOfTariffRef=VersionedRef(
                    version="fxc:v1.0", ref="fxc:point_to_point"
                ),
                TariffBasis="pointToPoint",
                fareStructureElements=[
                    FareStructureElement(
                        id="Tariff@AdultSingle@access",
                        version="1.0",
                        Name=MultilingualString(
                            value="O/D pairs for Line 15 Inbound",
                            lang=None,
                            textIdType=None,
                        ),
                        TypeOfFareStructureElementRef=VersionedRef(
                            version="fxc:v1.0",
                            ref="fxc:access",
                        ),
                        distanceMatrixElements=[
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
                        ],
                        GenericParameterAssignment=None,
                    ),
                ],
            ),
            id="Basic tariff",
        ),
    ],
)
def test_parse_tariff(xml_str: str, expected: Tariff) -> None:
    """Test parsing of tariff with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_tariff(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str",
    [
        pytest.param(
            """
            <Tariff>
                <Name>Test Tariff</Name>
                <OperatorRef version="1.0" ref="test" />
                <LineRef version="1.0" ref="test" />
                <TypeOfTariffRef version="1.0" ref="test" />
                <TariffBasis>test</TariffBasis>
            </Tariff>
            """,
            id="Missing ID and version",
        ),
        pytest.param(
            """
            <Tariff id="test">
                <Name>Test Tariff</Name>
                <OperatorRef version="1.0" ref="test" />
                <LineRef version="1.0" ref="test" />
                <TypeOfTariffRef version="1.0" ref="test" />
                <TariffBasis>test</TariffBasis>
            </Tariff>
            """,
            id="Missing version",
        ),
        pytest.param(
            """
            <Tariff version="1.0">
                <Name>Test Tariff</Name>
                <OperatorRef version="1.0" ref="test" />
                <LineRef version="1.0" ref="test" />
                <TypeOfTariffRef version="1.0" ref="test" />
                <TariffBasis>test</TariffBasis>
            </Tariff>
            """,
            id="Missing ID",
        ),
    ],
)
def test_parse_tariff_missing_attributes(xml_str: str) -> None:
    """Test parsing of tariff with missing required attributes."""
    elem = parse_xml_str_as_netex(xml_str)

    with pytest.raises(ValueError, match="Missing required id or version in Tariff"):
        parse_tariff(elem)
