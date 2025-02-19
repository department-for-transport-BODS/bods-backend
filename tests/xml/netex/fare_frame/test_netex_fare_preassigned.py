"""
Preassigned
"""

import pytest
from common_layer.xml.netex.models import AccessRightInProduct, VersionedRef
from common_layer.xml.netex.parser.fare_frame.netex_fare_preassigned import (
    parse_access_right_in_product,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                <ValidableElementRef version="1.0" ref="Trip@AdultSingle@travel" />
            </AccessRightInProduct>
            """,
            AccessRightInProduct(
                id="Trip@AdultSingle@travel@accessRight",
                version="1.0",
                order="1",
                ValidableElementRef=VersionedRef(
                    version="1.0", ref="Trip@AdultSingle@travel"
                ),
            ),
            id="Complete access right in product",
        ),
        pytest.param(
            """
            <AccessRightInProduct id="Trip@ChildSingle@travel@accessRight" version="2.0" order="2">
                <ValidableElementRef version="2.0" ref="Trip@ChildSingle@travel" />
            </AccessRightInProduct>
            """,
            AccessRightInProduct(
                id="Trip@ChildSingle@travel@accessRight",
                version="2.0",
                order="2",
                ValidableElementRef=VersionedRef(
                    version="2.0", ref="Trip@ChildSingle@travel"
                ),
            ),
            id="Access right with different version and order",
        ),
        pytest.param(
            """
            <AccessRightInProduct id="Trip@invalid@accessRight" version="1.0">
                <ValidableElementRef version="1.0" ref="Trip@invalid@travel" />
            </AccessRightInProduct>
            """,
            None,
            id="Invalid access right - missing order",
        ),
        pytest.param(
            """
            <AccessRightInProduct id="Trip@invalid@accessRight" version="1.0" order="1">
            </AccessRightInProduct>
            """,
            None,
            id="Invalid access right - missing ValidableElementRef",
        ),
    ],
)
def test_parse_access_right_in_product(
    xml_str: str, expected: AccessRightInProduct | None
) -> None:
    """Test parsing of access rights in product with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_access_right_in_product(elem)

    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert_model_equal(result, expected)
