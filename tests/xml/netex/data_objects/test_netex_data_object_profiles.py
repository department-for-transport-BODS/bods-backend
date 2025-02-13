"""
Profile Parsing Tests
"""

import pytest
from common_layer.xml.netex.models import CompanionProfile, UserProfile, VersionedRef
from common_layer.xml.netex.parser import parse_companion_profile, parse_user_profile
from lxml.etree import fromstring

from tests.xml.conftest import assert_model_equal


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <CompanionProfile version="fxc:v1.0" id="fxc:adult@infant">
                <UserProfileRef ref="fxc:infant" version="fxc:v1.0"/>
                <MinimumNumberOfPersons>0</MinimumNumberOfPersons>
                <MaximumNumberOfPersons>3</MaximumNumberOfPersons>
            </CompanionProfile>
            """,
            CompanionProfile(
                id="fxc:adult@infant",
                version="fxc:v1.0",
                UserProfileRef=VersionedRef(version="fxc:v1.0", ref="fxc:infant"),
                MinimumNumberOfPersons=0,
                MaximumNumberOfPersons=3,
                DiscountBasis=None,
            ),
            id="Basic companion profile",
        ),
        pytest.param(
            """
            <CompanionProfile version="fxc:v1.0" id="fxc:adult@child">
                <UserProfileRef ref="fxc:child" version="fxc:v1.0"/>
                <MinimumNumberOfPersons>1</MinimumNumberOfPersons>
                <MaximumNumberOfPersons>2</MaximumNumberOfPersons>
                <DiscountBasis>percentage</DiscountBasis>
            </CompanionProfile>
            """,
            CompanionProfile(
                id="fxc:adult@child",
                version="fxc:v1.0",
                UserProfileRef=VersionedRef(version="fxc:v1.0", ref="fxc:child"),
                MinimumNumberOfPersons=1,
                MaximumNumberOfPersons=2,
                DiscountBasis="percentage",
            ),
            id="Companion profile with discount basis",
        ),
        pytest.param(
            """
            <CompanionProfile version="fxc:v1.0" id="fxc:adult@senior">
                <UserProfileRef ref="fxc:senior" version="fxc:v1.0"/>
                <MinimumNumberOfPersons>0</MinimumNumberOfPersons>
                <MaximumNumberOfPersons>1</MaximumNumberOfPersons>
                <UnknownTag>Some content</UnknownTag>
            </CompanionProfile>
            """,
            CompanionProfile(
                id="fxc:adult@senior",
                version="fxc:v1.0",
                UserProfileRef=VersionedRef(version="fxc:v1.0", ref="fxc:senior"),
                MinimumNumberOfPersons=0,
                MaximumNumberOfPersons=1,
                DiscountBasis=None,
            ),
            id="Companion profile with unknown tag",
        ),
    ],
)
def test_parse_companion_profile(xml_str: str, expected: CompanionProfile) -> None:
    """Test parsing of companion profile with various inputs."""
    elem = fromstring(xml_str.strip())
    result = parse_companion_profile(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <UserProfile version="fxc:v1.0" id="fxc:adult">
                <Name>Adult</Name>
                <TypeOfConcessionRef version="fxc:v1.0" ref="fxc:none"/>
                <companionProfiles>
                    <CompanionProfile version="fxc:v1.0" id="fxc:adult@infant">
                        <UserProfileRef ref="fxc:infant" version="fxc:v1.0"/>
                        <MinimumNumberOfPersons>0</MinimumNumberOfPersons>
                        <MaximumNumberOfPersons>3</MaximumNumberOfPersons>
                    </CompanionProfile>
                </companionProfiles>
            </UserProfile>
            """,
            UserProfile(
                id="fxc:adult",
                version="fxc:v1.0",
                Name="Adult",
                TypeOfConcessionRef=VersionedRef(version="fxc:v1.0", ref="fxc:none"),
                companionProfiles=[
                    CompanionProfile(
                        id="fxc:adult@infant",
                        version="fxc:v1.0",
                        UserProfileRef=VersionedRef(
                            version="fxc:v1.0", ref="fxc:infant"
                        ),
                        MinimumNumberOfPersons=0,
                        MaximumNumberOfPersons=3,
                        DiscountBasis=None,
                    )
                ],
            ),
            id="Adult profile with companion profiles",
        ),
        pytest.param(
            """
            <UserProfile version="fxc:v1.0" id="fxc:child">
                <Name>Child</Name>
                <TypeOfConcessionRef version="fxc:v1.0" ref="fxc:child"/>
                <MinimumAge>5</MinimumAge>
                <MaximumAge>15</MaximumAge>
            </UserProfile>
            """,
            UserProfile(
                id="fxc:child",
                version="fxc:v1.0",
                Name="Child",
                TypeOfConcessionRef=VersionedRef(version="fxc:v1.0", ref="fxc:child"),
                MinimumAge=5,
                MaximumAge=15,
            ),
            id="Child profile with age restrictions",
        ),
        pytest.param(
            """
            <UserProfile version="fxc:v1.0" id="fxc:infant">
                <Name>Infant</Name>
                <Description>Under 5 years</Description>
                <TypeOfConcessionRef version="fxc:v1.0" ref="fxc:infant"/>
                <MinimumAge>0</MinimumAge>
                <MaximumAge>4</MaximumAge>
                <DiscountBasis>free</DiscountBasis>
                <companionProfiles>
                    <CompanionProfile id="fxc:infant@adult" version="fxc:v1.0">
                        <UserProfileRef ref="fxc:adult" version="fxc:v1.0"/>
                        <MinimumNumberOfPersons>1</MinimumNumberOfPersons>
                        <MaximumNumberOfPersons>1</MaximumNumberOfPersons>
                        <DiscountBasis>none</DiscountBasis>
                    </CompanionProfile>
                </companionProfiles>
            </UserProfile>
            """,
            UserProfile(
                id="fxc:infant",
                version="fxc:v1.0",
                Name="Infant",
                Description="Under 5 years",
                TypeOfConcessionRef=VersionedRef(version="fxc:v1.0", ref="fxc:infant"),
                MinimumAge=0,
                MaximumAge=4,
                DiscountBasis="free",
                companionProfiles=[
                    CompanionProfile(
                        id="fxc:infant@adult",
                        version="fxc:v1.0",
                        UserProfileRef=VersionedRef(
                            version="fxc:v1.0", ref="fxc:adult"
                        ),
                        MinimumNumberOfPersons=1,
                        MaximumNumberOfPersons=1,
                        DiscountBasis="none",
                    )
                ],
            ),
            id="Infant profile with full details",
        ),
        pytest.param(
            """
            <UserProfile version="fxc:v1.0" id="fxc:senior">
                <Name>Senior</Name>
                <TypeOfConcessionRef version="fxc:v1.0" ref="fxc:senior"/>
                <ProofRequired>membershipCard</ProofRequired>
                <DiscountBasis>discount</DiscountBasis>
            </UserProfile>
            """,
            UserProfile(
                id="fxc:senior",
                version="fxc:v1.0",
                Name="Senior",
                TypeOfConcessionRef=VersionedRef(version="fxc:v1.0", ref="fxc:senior"),
                ProofRequired="membershipCard",
                DiscountBasis="discount",
            ),
            id="Senior profile with proof required",
        ),
    ],
)
def test_parse_user_profile(xml_str: str, expected: UserProfile) -> None:
    """Test parsing of user profile with various inputs."""
    elem = fromstring(xml_str.strip())
    result = parse_user_profile(elem)
    assert_model_equal(result, expected)
