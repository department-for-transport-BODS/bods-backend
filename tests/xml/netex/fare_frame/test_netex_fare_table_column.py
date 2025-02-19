"""
Test Parsing Fare Tables
"""

import pytest
from common_layer.xml.netex.models import (
    MultilingualString,
    ObjectReferences,
    VersionedRef,
)
from common_layer.xml.netex.models.fare_frame.netex_fare_table import FareTableColumn
from common_layer.xml.netex.parser.fare_frame import parse_fare_table_column

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <FareTableColumn id="Trip@AdultSingle-SOP@Line_15@c1@1501" version="1.0" order="1">
                <Name>Ilkeston</Name>
                <representing>
                    <FareZoneRef version="1.0" ref="fs@1501" />
                </representing>
            </FareTableColumn>
            """,
            FareTableColumn(
                id="Trip@AdultSingle-SOP@Line_15@c1@1501",
                version="1.0",
                order="1",
                Name=MultilingualString(value="Ilkeston", lang=None, textIdType=None),
                representing=ObjectReferences(
                    FareZoneRef=VersionedRef(version="1.0", ref="fs@1501")
                ),
            ),
            id="Basic fare table column",
        ),
        pytest.param(
            """
            <FareTableColumn id="Trip@AdultSingle-SOP@Line_15@c1@1501" version="1.0" order="1">
                <Name>Ilkeston</Name>
                <representing>
                    <FareZoneRef version="1.0" ref="fs@1501" />
                    <LineRef version="1.0" ref="Line_15" />
                </representing>
            </FareTableColumn>
            """,
            FareTableColumn(
                id="Trip@AdultSingle-SOP@Line_15@c1@1501",
                version="1.0",
                order="1",
                Name=MultilingualString(value="Ilkeston", lang=None, textIdType=None),
                representing=ObjectReferences(
                    FareZoneRef=VersionedRef(version="1.0", ref="fs@1501"),
                    LineRef=VersionedRef(version="1.0", ref="Line_15"),
                ),
            ),
            id="Column with multiple representing refs",
        ),
        pytest.param(
            """
            <FareTableColumn id="Trip@AdultSingle-SOP@Line_15@c1@1501" version="1.0" order="1">
                <Name>Ilkeston</Name>
                <representing>
                    <FareZoneRef version="1.0" ref="fs@1501" />
                </representing>
                <UnknownTag>Some content</UnknownTag>
            </FareTableColumn>
            """,
            FareTableColumn(
                id="Trip@AdultSingle-SOP@Line_15@c1@1501",
                version="1.0",
                order="1",
                Name=MultilingualString(value="Ilkeston", lang=None, textIdType=None),
                representing=ObjectReferences(
                    FareZoneRef=VersionedRef(version="1.0", ref="fs@1501")
                ),
            ),
            id="Column with unknown tag",
        ),
    ],
)
def test_parse_fare_table_column(xml_str: str, expected: FareTableColumn) -> None:
    """Test parsing of fare table column with various valid inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_fare_table_column(elem)
    assert result is not None
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str",
    [
        pytest.param(
            """
            <FareTableColumn id="Trip@AdultSingle-SOP@Line_15@c1@1501" version="1.0">
                <Name>Ilkeston</Name>
                <representing>
                    <FareZoneRef version="1.0" ref="fs@1501" />
                </representing>
            </FareTableColumn>
            """,
            id="Column missing order",
        ),
        pytest.param(
            """
            <FareTableColumn id="Trip@AdultSingle-SOP@Line_15@c1@1501" version="1.0" order="1">
                <representing>
                    <FareZoneRef version="1.0" ref="fs@1501" />
                </representing>
            </FareTableColumn>
            """,
            id="Column missing name",
        ),
        pytest.param(
            """
            <FareTableColumn version="1.0" order="1">
                <Name>Ilkeston</Name>
                <representing>
                    <FareZoneRef version="1.0" ref="fs@1501" />
                </representing>
            </FareTableColumn>
            """,
            id="Column missing id",
        ),
    ],
)
def test_parse_fare_table_column_errors(xml_str: str) -> None:
    """Test parsing of fare table column with invalid inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_fare_table_column(elem)
    assert result is None
