"""
Test FareStructure
"""

import pytest
from common_layer.xml.netex.models import (
    DistanceMatrixElement,
    FrequencyOfUse,
    GenericParameterAssignment,
    RoundTrip,
    UsageValidityPeriod,
    UserProfile,
    ValidityParameters,
    VersionedRef,
)
from common_layer.xml.netex.parser import (
    parse_distance_matrix_element,
    parse_frequency_of_use,
    parse_generic_parameter_assignment,
    parse_round_trip,
    parse_usage_validity_period,
    parse_validity_parameters,
)
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


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <UsageValidityPeriod id="uvp1" version="1.0">
                <UsageTrigger>startOutboundRide</UsageTrigger>
                <UsageEnd>endOutboundRide</UsageEnd>
                <ActivationMeans>checkIn</ActivationMeans>
            </UsageValidityPeriod>
            """,
            UsageValidityPeriod(
                id="uvp1",
                version="1.0",
                UsageTrigger="startOutboundRide",
                UsageEnd="endOutboundRide",
                ActivationMeans="checkIn",
            ),
            id="Complete usage validity period",
        ),
        pytest.param(
            """
            <UsageValidityPeriod id="uvp1" version="1.0">
                <UsageTrigger>startOutboundRide</UsageTrigger>
            </UsageValidityPeriod>
            """,
            None,
            id="Missing required fields",
            marks=pytest.mark.xfail(raises=ValueError, strict=True),
        ),
    ],
)
def test_parse_usage_validity_period(
    xml_str: str, expected: UsageValidityPeriod
) -> None:
    """Test parsing of usage validity period."""
    elem = fromstring(xml_str.strip())
    result = parse_usage_validity_period(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <FrequencyOfUse id="freq1" version="1.0">
                <FrequencyOfUseType>single</FrequencyOfUseType>
            </FrequencyOfUse>
            """,
            FrequencyOfUse(id="freq1", version="1.0", FrequencyOfUseType="single"),
            id="Complete frequency of use",
        ),
        pytest.param(
            """
            <FrequencyOfUse id="freq1" version="1.0">
            </FrequencyOfUse>
            """,
            None,
            id="Missing frequency type",
            marks=pytest.mark.xfail(raises=ValueError, strict=True),
        ),
    ],
)
def test_parse_frequency_of_use(xml_str: str, expected: FrequencyOfUse) -> None:
    """Test parsing of frequency of use."""
    elem = fromstring(xml_str.strip())
    result = parse_frequency_of_use(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <RoundTrip id="rt1" version="1.0">
                <TripType>return</TripType>
            </RoundTrip>
            """,
            RoundTrip(id="rt1", version="1.0", TripType="return"),
            id="Complete round trip",
        ),
        pytest.param(
            """
            <RoundTrip id="rt1" version="1.0">
            </RoundTrip>
            """,
            None,
            id="Missing trip type",
            marks=pytest.mark.xfail(raises=ValueError, strict=True),
        ),
    ],
)
def test_parse_round_trip(xml_str: str, expected: RoundTrip) -> None:
    """Test parsing of round trip."""
    elem = fromstring(xml_str.strip())
    result = parse_round_trip(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <validityParameters>
                <LineRef version="1.0" ref="op:501#PH0006652:5#25/04/2022"/>
            </validityParameters>
            """,
            ValidityParameters(
                LineRef=VersionedRef(version="1.0", ref="op:501#PH0006652:5#25/04/2022")
            ),
            id="Complete validity parameters",
        ),
        pytest.param(
            """
            <validityParameters>
            </validityParameters>
            """,
            None,
            id="Missing line reference",
            marks=pytest.mark.xfail(raises=ValueError, strict=True),
        ),
    ],
)
def test_parse_validity_parameters(xml_str: str, expected: ValidityParameters) -> None:
    """Test parsing of validity parameters."""
    elem = fromstring(xml_str.strip())
    result = parse_validity_parameters(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <GenericParameterAssignment id="Tariff@Term_Ticket_501@access_lines" version="1.0" order="1">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access"/>
                <ValidityParameterAssignmentType>OR</ValidityParameterAssignmentType>
                <validityParameters>
                    <LineRef version="1.0" ref="op:501#PH0006652:5#25/04/2022"/>
                </validityParameters>
            </GenericParameterAssignment>
            """,
            GenericParameterAssignment(
                id="Tariff@Term_Ticket_501@access_lines",
                version="1.0",
                order="1",
                TypeOfAccessRightAssignmentRef=VersionedRef(
                    version="fxc:v1.0", ref="fxc:can_access"
                ),
                ValidityParameterAssignmentType="OR",
                validityParameters=ValidityParameters(
                    LineRef=VersionedRef(
                        version="1.0", ref="op:501#PH0006652:5#25/04/2022"
                    )
                ),
                limitations=None,
                LimitationGroupingType=None,
            ),
            id="Parameter assignment with validity parameters",
        ),
        pytest.param(
            """
            <GenericParameterAssignment id="Tariff@adult" version="1.0" order="1">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible"/>
                <LimitationGroupingType>XOR</LimitationGroupingType>
                <limitations>
                    <UserProfile version="1.0" id="adult">
                        <Name>Adult</Name>
                        <UserType>adult</UserType>
                    </UserProfile>
                </limitations>
            </GenericParameterAssignment>
            """,
            GenericParameterAssignment(
                id="Tariff@adult",
                version="1.0",
                order="1",
                TypeOfAccessRightAssignmentRef=VersionedRef(
                    version="fxc:v1.0", ref="fxc:eligible"
                ),
                LimitationGroupingType="XOR",
                limitations=[
                    UserProfile(
                        id="adult", version="1.0", Name="Adult", UserType="adult"  # type: ignore
                    )
                ],
                ValidityParameterAssignmentType=None,
                validityParameters=None,
            ),
            id="Parameter assignment with limitations",
        ),
        pytest.param(
            """
            <GenericParameterAssignment id="test" version="1.0" order="1">
            </GenericParameterAssignment>
            """,
            None,
            id="Missing required access right reference",
            marks=pytest.mark.xfail(raises=ValueError, strict=True),
        ),
    ],
)
def test_parse_generic_parameter_assignment(
    xml_str: str, expected: GenericParameterAssignment
) -> None:
    """Test parsing of generic parameter assignment."""
    elem = fromstring(xml_str.strip())
    result = parse_generic_parameter_assignment(elem)
    assert_model_equal(result, expected)
