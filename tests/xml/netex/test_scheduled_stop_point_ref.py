"""
Test Custom Parsing Class
"""

import pytest
from common_layer.xml.netex.models import ScheduledStopPointReference
from common_layer.xml.netex.parser.netex_scheduled_stop_point_ref import (
    parse_scheduled_stop_point_ref,
    parse_scheduled_stop_point_refs,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "ref, version, name, expected_atco_code",
    [
        pytest.param(
            "atco:1000DINR5456",
            "any",
            "Test Stop",
            "1000DINR5456",
            id="Valid ATCO reference",
        ),
        pytest.param("xyz:987", "any", "Other Stop", None, id="Non-ATCO reference"),
        pytest.param(
            "simple_ref", "any", "Simple Stop", None, id="Reference without colon"
        ),
        pytest.param(
            "atco:2000ABCD1234",
            "1.0",
            "Another Stop",
            "2000ABCD1234",
            id="Another ATCO reference",
        ),
    ],
)
def test_scheduled_stop_point_reference_atco_code(
    ref, version, name, expected_atco_code
):
    """
    Test Parsing of the AtcoCodes
    """
    ref_obj = ScheduledStopPointReference(ref=ref, version=version, Name=name)
    assert ref_obj.atco_code == expected_atco_code
    assert ref_obj.ref == ref
    assert ref_obj.Name == name


@pytest.mark.parametrize(
    "ref, version, expected_atco_code",
    [
        pytest.param(
            "atco:1000DINR5456",
            "any",
            "1000DINR5456",
            id="ATCO reference with minimal data",
        ),
        pytest.param("xyz:987", "any", None, id="Non-ATCO reference with minimal data"),
    ],
)
def test_scheduled_stop_point_reference_incomplete_data(
    ref, version, expected_atco_code
):
    """
    Test Error case when it's not defined as atco code
    """
    ref_obj = ScheduledStopPointReference(ref=ref, version=version)
    assert ref_obj.atco_code == expected_atco_code
    assert ref_obj.Name is None


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <ScheduledStopPointRef ref="atco:1000DINR5456" version="any">Brooke Street</ScheduledStopPointRef>
            """,
            ScheduledStopPointReference(
                ref="atco:1000DINR5456",
                version="any",
                Name="Brooke Street",
                atco_code="1000DINR5456",
            ),
            id="Valid ATCO ScheduledStopPointRef",
        ),
        pytest.param(
            """
            <ScheduledStopPointRef ref="xyz:987" version="1.0">Other Stop</ScheduledStopPointRef>
            """,
            ScheduledStopPointReference(
                ref="xyz:987", version="1.0", Name="Other Stop", atco_code=None
            ),
            id="Non-ATCO ScheduledStopPointRef",
        ),
        pytest.param(
            """
            <TimingPointRef ref="timing:123" version="1.0">Timing Point</TimingPointRef>
            """,
            None,
            id="Non-ScheduledStopPointRef element",
        ),
    ],
)
def test_parse_scheduled_stop_point_ref(
    xml_str: str, expected: ScheduledStopPointReference | None
) -> None:
    """Test parsing of individual ScheduledStopPointRef elements."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_scheduled_stop_point_ref(elem)

    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <members>
                <ScheduledStopPointRef ref="atco:1000DINR5456" version="any">Brooke Street</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DINR5491" version="any">Dale Street</ScheduledStopPointRef>
                <TimingPointRef ref="timing:123" version="1.0">Timing Point</TimingPointRef>
            </members>
            """,
            [
                ScheduledStopPointReference(
                    ref="atco:1000DINR5456",
                    version="any",
                    Name="Brooke Street",
                    atco_code="1000DINR5456",
                ),
                ScheduledStopPointReference(
                    ref="atco:1000DINR5491",
                    version="any",
                    Name="Dale Street",
                    atco_code="1000DINR5491",
                ),
            ],
            id="Multiple ScheduledStopPointRefs",
        ),
        pytest.param(
            """
            <members>
                <TimingPointRef ref="timing:123" version="1.0">Timing Point</TimingPointRef>
            </members>
            """,
            [],
            id="No ScheduledStopPointRefs",
        ),
    ],
)
def test_parse_scheduled_stop_point_refs(
    xml_str: str, expected: list[ScheduledStopPointReference]
) -> None:
    """Test parsing of multiple ScheduledStopPointRef elements."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_scheduled_stop_point_refs(elem)

    assert len(result) == len(expected)

    for res, exp in zip(result, expected):
        assert_model_equal(res, exp)
