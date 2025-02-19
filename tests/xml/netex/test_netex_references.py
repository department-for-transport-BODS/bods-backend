"""
Test Reference Parsing
"""

import pytest
from common_layer.xml.netex.models import (
    ObjectReferences,
    PointRefs,
    PricableObjectRefs,
    ScheduledStopPointReference,
    VersionedRef,
)
from common_layer.xml.netex.parser import (
    parse_object_references,
    parse_point_refs,
    parse_pricable_object_refs,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <objectReferences>
                <OperatorRef version="1.0" ref="noc:BRTB" />
                <LineRef version="1.0" ref="BRTB:PC0003375:3:15" />
            </objectReferences>
            """,
            ObjectReferences(
                OperatorRef=VersionedRef(version="1.0", ref="noc:BRTB"),
                LineRef=VersionedRef(version="1.0", ref="BRTB:PC0003375:3:15"),
            ),
            id="Valid object references",
        ),
        pytest.param(
            """
            <objectReferences>
                <OperatorRef version="2.0" ref="operator1" />
                <LineRef version="2.0" ref="line1" />
                <UnknownRef version="1.0" ref="something" />
            </objectReferences>
            """,
            ObjectReferences(
                OperatorRef=VersionedRef(version="2.0", ref="operator1"),
                LineRef=VersionedRef(version="2.0", ref="line1"),
            ),
            id="Object references with unknown tag",
        ),
    ],
)
def test_parse_object_references(xml_str: str, expected: ObjectReferences) -> None:
    """Test parsing of object references with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_object_references(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <pricesFor>
                <PreassignedFareProductRef version="1.0" ref="Trip@AdultSingle" />
                <SalesOfferPackageRef version="1.0" ref="Trip@AdultSingle-SOP@Onboard" />
                <UserProfileRef ref="Pass:UserProfile:adult" version="1.0" />
            </pricesFor>
            """,
            PricableObjectRefs(
                PreassignedFareProductRef=VersionedRef(
                    version="1.0", ref="Trip@AdultSingle"
                ),
                SalesOfferPackageRef=VersionedRef(
                    version="1.0", ref="Trip@AdultSingle-SOP@Onboard"
                ),
                UserProfileRef=VersionedRef(
                    version="1.0", ref="Pass:UserProfile:adult"
                ),
            ),
            id="Complete price references",
        ),
        pytest.param(
            """
            <pricesFor>
                <PreassignedFareProductRef version="1.0" ref="op:Pass@Term_Ticket_Totnes_506_schoolPupil"/>
            </pricesFor>
            """,
            PricableObjectRefs(
                PreassignedFareProductRef=VersionedRef(
                    version="1.0", ref="op:Pass@Term_Ticket_Totnes_506_schoolPupil"
                ),
                SalesOfferPackageRef=None,
                UserProfileRef=None,
            ),
            id="Minimal price references",
        ),
        pytest.param(
            """
            <pricesFor>
                <PreassignedFareProductRef version="1.0" ref="Trip@AdultSingle" />
                <UnknownRef version="1.0" ref="something" />
                <UserProfileRef ref="Pass:UserProfile:adult" version="1.0" />
            </pricesFor>
            """,
            PricableObjectRefs(
                PreassignedFareProductRef=VersionedRef(
                    version="1.0", ref="Trip@AdultSingle"
                ),
                SalesOfferPackageRef=None,
                UserProfileRef=VersionedRef(
                    version="1.0", ref="Pass:UserProfile:adult"
                ),
            ),
            id="Price references with unknown tag",
        ),
    ],
)
def test_parse_pricable_object_refs(xml_str: str, expected: PricableObjectRefs) -> None:
    """Test parsing of pricable object references with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_pricable_object_refs(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <members>
                <ScheduledStopPointRef ref="atco:1000DINR5456" version="any">Brooke Street</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DINR5491" version="any">Dale Street</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DINR5451" version="any">Manners Street</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DISS5490" version="any">South Street</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DIWR5593" version="any">Ilkeston Market Place</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DINR5493" version="any">Kensington School</ScheduledStopPointRef>
            </members>
            """,
            PointRefs(
                ScheduledStopPointRef=[
                    ScheduledStopPointReference(
                        version="any",
                        ref="atco:1000DINR5456",
                        Name="Brooke Street",
                        atco_code="1000DINR5456",
                    ),
                    ScheduledStopPointReference(
                        version="any",
                        ref="atco:1000DINR5491",
                        Name="Dale Street",
                        atco_code="1000DINR5491",
                    ),
                    ScheduledStopPointReference(
                        version="any",
                        ref="atco:1000DINR5451",
                        Name="Manners Street",
                        atco_code="1000DINR5451",
                    ),
                    ScheduledStopPointReference(
                        version="any",
                        ref="atco:1000DISS5490",
                        Name="South Street",
                        atco_code="1000DISS5490",
                    ),
                    ScheduledStopPointReference(
                        version="any",
                        ref="atco:1000DIWR5593",
                        Name="Ilkeston Market Place",
                        atco_code="1000DIWR5593",
                    ),
                    ScheduledStopPointReference(
                        version="any",
                        ref="atco:1000DINR5493",
                        Name="Kensington School",
                        atco_code="1000DINR5493",
                    ),
                ],
                TimingPointRef=[],
                RoutePointRef=[],
                FareScheduledStopPointRef=[],
                PointRef=[],
            ),
            id="Multiple scheduled stop points",
        ),
        pytest.param(
            """
            <members>
                <ScheduledStopPointRef ref="atco:1000DINR5456" version="1.0">Stop A</ScheduledStopPointRef>
                <TimingPointRef ref="timing:123" version="1.0">Timing Point 1</TimingPointRef>
                <FareScheduledStopPointRef ref="fare:456" version="1.0">Fare Stage 1</FareScheduledStopPointRef>
            </members>
            """,
            PointRefs(
                ScheduledStopPointRef=[
                    ScheduledStopPointReference(
                        version="1.0",
                        ref="atco:1000DINR5456",
                        Name="Stop A",
                        atco_code="1000DINR5456",
                    )
                ],
                TimingPointRef=[VersionedRef(version="1.0", ref="timing:123")],
                FareScheduledStopPointRef=[VersionedRef(version="1.0", ref="fare:456")],
                RoutePointRef=[],
                PointRef=[],
            ),
            id="Mixed point types",
        ),
        pytest.param(
            """
            <members>
                <UnknownRef ref="unknown:789" version="1.0">Unknown Point</UnknownRef>
                <ScheduledStopPointRef ref="atco:1000DINR5456" version="1.0">Valid Stop</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="xyz:987" version="1.0">Other Stop</ScheduledStopPointRef>
            </members>
            """,
            PointRefs(
                ScheduledStopPointRef=[
                    ScheduledStopPointReference(
                        version="1.0",
                        ref="atco:1000DINR5456",
                        Name="Valid Stop",
                        atco_code="1000DINR5456",
                    ),
                    ScheduledStopPointReference(
                        version="1.0", ref="xyz:987", Name="Other Stop", atco_code=None
                    ),
                ],
                TimingPointRef=[],
                RoutePointRef=[],
                FareScheduledStopPointRef=[],
                PointRef=[],
            ),
            id="Mixed point types with non-atco ref",
        ),
    ],
)
def test_parse_point_refs(xml_str: str, expected: PointRefs) -> None:
    """Test parsing of point references with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_point_refs(elem)
    assert_model_equal(result, expected)
