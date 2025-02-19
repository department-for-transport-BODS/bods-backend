"""
FareFrame FareStructure
"""

import pytest
from common_layer.xml.netex.models import (
    DistanceMatrixElement,
    FareStructureElement,
    FrequencyOfUse,
    GenericParameterAssignment,
    MultilingualString,
    RoundTrip,
    UserProfile,
    ValidityParameters,
    VersionedRef,
)
from common_layer.xml.netex.parser import (
    parse_fare_structure_element,
    parse_frequency_of_use,
    parse_generic_parameter_assignment,
    parse_round_trip,
    parse_validity_parameters,
)
from common_layer.xml.netex.parser.fare_frame.netex_fare_tariff import (
    parse_fare_structure_elements,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


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
    elem = parse_xml_str_as_netex(xml_str)
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
    elem = parse_xml_str_as_netex(xml_str)
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
    ],
)
def test_parse_validity_parameters(
    xml_str: str, expected: ValidityParameters | None
) -> None:
    """Test parsing of validity parameters."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_validity_parameters(elem)
    if result is None or expected is None:
        assert result is None
    else:
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
                        id="adult",
                        version="1.0",
                        Name=MultilingualString(
                            value="Adult", lang=None, textIdType=None
                        ),
                        UserType="adult",
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
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_generic_parameter_assignment(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
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
                <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
                    <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
                    <ValidityParameterAssignmentType>EQ</ValidityParameterAssignmentType>
                </GenericParameterAssignment>
            </FareStructureElement>
            """,
            FareStructureElement(
                id="Tariff@AdultSingle@access",
                version="1.0",
                Name=MultilingualString(
                    value="O/D pairs for Line 15 Inbound", lang=None, textIdType=None
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
                GenericParameterAssignment=GenericParameterAssignment(
                    id="Tariff@AdultSingle@access",
                    version="1.0",
                    order="01",
                    TypeOfAccessRightAssignmentRef=VersionedRef(
                        version="fxc:v1.0",
                        ref="fxc:can_access",
                    ),
                    ValidityParameterAssignmentType="EQ",
                    LimitationGroupingType=None,
                    validityParameters=None,
                    limitations=None,
                ),
            ),
            id="Basic fare structure element with distance matrix",
        ),
        pytest.param(
            """
            <FareStructureElement id="Tariff@AdultSingle@conditions_of_travel" version="1.0">
                <Name>Conditions of travel</Name>
                <TypeOfFareStructureElementRef version="fxc:v1.0" ref="fxc:travel_conditions" />
                <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                    <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
                    <LimitationGroupingType>AND</LimitationGroupingType>
                    <limitations>
                        <RoundTrip version="1.0" id="Trip@travel@condition@direction">
                            <TripType>single</TripType>
                        </RoundTrip>
                        <FrequencyOfUse version="1.0" id="Pass@AdultSingle@frequency">
                            <FrequencyOfUseType>single</FrequencyOfUseType>
                        </FrequencyOfUse>
                    </limitations>
                </GenericParameterAssignment>
            </FareStructureElement>
            """,
            FareStructureElement(
                id="Tariff@AdultSingle@conditions_of_travel",
                version="1.0",
                Name=MultilingualString(
                    value="Conditions of travel", lang=None, textIdType=None
                ),
                TypeOfFareStructureElementRef=VersionedRef(
                    version="fxc:v1.0",
                    ref="fxc:travel_conditions",
                ),
                distanceMatrixElements=None,
                GenericParameterAssignment=GenericParameterAssignment(
                    id="Tariff@AdultSingle@conditions_of_travel",
                    version="1.0",
                    order="1",
                    TypeOfAccessRightAssignmentRef=VersionedRef(
                        version="fxc:v1.0",
                        ref="fxc:condition_of_use",
                    ),
                    ValidityParameterAssignmentType=None,
                    LimitationGroupingType="AND",
                    validityParameters=None,
                    limitations=[
                        RoundTrip(
                            id="Trip@travel@condition@direction",
                            version="1.0",
                            TripType="single",
                        ),
                        FrequencyOfUse(
                            id="Pass@AdultSingle@frequency",
                            version="1.0",
                            FrequencyOfUseType="single",
                        ),
                    ],
                ),
            ),
            id="Fare structure element with limitations",
        ),
    ],
)
def test_parse_fare_structure_element(
    xml_str: str, expected: FareStructureElement
) -> None:
    """Test parsing of fare structure element with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_fare_structure_element(elem)
    assert_model_equal(result, expected)


def test_parse_fare_structure_element_missing_attributes() -> None:
    """Test parsing of fare structure element with missing required attributes."""
    xml_str = """
        <FareStructureElement>
            <Name>Test Element</Name>
            <TypeOfFareStructureElementRef version="1.0" ref="test" />
        </FareStructureElement>
        """
    elem = parse_xml_str_as_netex(xml_str)

    with pytest.raises(
        ValueError, match="Missing required id or version in FareStructureElement"
    ):
        parse_fare_structure_element(elem)


def test_parse_fare_structure_element_missing_name() -> None:
    """Test parsing of fare structure element with missing name."""
    xml_str = """
        <FareStructureElement id="test" version="1.0">
            <TypeOfFareStructureElementRef version="1.0" ref="test" />
        </FareStructureElement>
        """
    elem = parse_xml_str_as_netex(xml_str)

    with pytest.raises(
        ValueError, match="Missing required Name in FareStructureElement"
    ):
        parse_fare_structure_element(elem)


def test_parse_fare_structure_element_missing_type_ref() -> None:
    """Test parsing of fare structure element with missing type reference."""
    xml_str = """
        <FareStructureElement id="test" version="1.0">
            <Name>Test Element</Name>
        </FareStructureElement>
        """
    elem = parse_xml_str_as_netex(xml_str)

    with pytest.raises(
        ValueError,
        match="Missing required TypeOfFareStructureElementRef in FareStructureElement",
    ):
        parse_fare_structure_element(elem)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <fareStructureElements>
                <FareStructureElement id="test1" version="1.0">
                    <Name>Test Element 1</Name>
                    <TypeOfFareStructureElementRef version="1.0" ref="test" />
                </FareStructureElement>
                <UnknownTag>Something</UnknownTag>
            </fareStructureElements>
            """,
            [
                FareStructureElement(
                    id="test1",
                    version="1.0",
                    Name="Test Element 1",
                    TypeOfFareStructureElementRef=VersionedRef(
                        version="1.0",
                        ref="test",
                    ),
                    distanceMatrixElements=None,
                    GenericParameterAssignment=None,
                ),
            ],
            id="Basic fare structure elements with unknown tag",
        ),
        pytest.param(
            """
            <fareStructureElements>
            </fareStructureElements>
            """,
            [],
            id="Empty fare structure elements",
        ),
    ],
)
def test_parse_fare_structure_elements(
    xml_str: str, expected: list[FareStructureElement]
) -> None:
    """Test parsing of fare structure elements with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_fare_structure_elements(elem)

    for result_element, expected_element in zip(result, expected):
        assert_model_equal(result_element, expected_element)
