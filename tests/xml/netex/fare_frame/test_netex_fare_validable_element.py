"""
ValidableElement
"""

import pytest
from common_layer.xml.netex.models import MultilingualString, VersionedRef
from common_layer.xml.netex.models.fare_frame.netex_fare_preassigned import (
    ValidableElement,
)
from common_layer.xml.netex.parser.fare_frame.netex_fare_validable_element import (
    parse_validable_element,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                <Name>Adult Single</Name>
                <fareStructureElements>
                    <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access" />
                    <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@conditions_of_travel" />
                </fareStructureElements>
            </ValidableElement>
            """,
            ValidableElement(
                id="Trip@AdultSingle@travel",
                version="1.0",
                Name=MultilingualString(value="Adult Single"),
                fareStructureElements=[
                    VersionedRef(version="1.0", ref="Tariff@AdultSingle@access"),
                    VersionedRef(
                        version="1.0", ref="Tariff@AdultSingle@conditions_of_travel"
                    ),
                ],
            ),
            id="Complete validable element with multiple fare structure elements",
        ),
        pytest.param(
            """
            <ValidableElement id="Trip@ChildSingle@travel" version="1.0">
                <Name lang="en">Child Single</Name>
                <fareStructureElements>
                    <FareStructureElementRef version="1.0" ref="Tariff@ChildSingle@access" />
                </fareStructureElements>
            </ValidableElement>
            """,
            ValidableElement(
                id="Trip@ChildSingle@travel",
                version="1.0",
                Name=MultilingualString(value="Child Single", lang="en"),
                fareStructureElements=[
                    VersionedRef(version="1.0", ref="Tariff@ChildSingle@access"),
                ],
            ),
            id="Validable element with language tag and single fare structure element",
        ),
        pytest.param(
            """
            <ValidableElement id="Trip@empty@travel" version="1.0">
                <Name>Empty Structure</Name>
                <fareStructureElements/>
            </ValidableElement>
            """,
            ValidableElement(
                id="Trip@empty@travel",
                version="1.0",
                Name=MultilingualString(value="Empty Structure"),
                fareStructureElements=[],
            ),
            id="Validable element with no fare structure elements",
        ),
    ],
)
def test_parse_validable_element(xml_str: str, expected: ValidableElement) -> None:
    """Test parsing of validable elements with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_validable_element(elem)
    assert result is not None
    assert_model_equal(result, expected)
