"""
Test Parsing Fare Table Rows
"""

import pytest
from common_layer.xml.netex.models import MultilingualString
from common_layer.xml.netex.models.fare_frame.netex_fare_table import FareTableRow
from common_layer.xml.netex.parser.fare_frame.netex_fare_table_row import (
    parse_fare_table_row,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <FareTableRow id="Trip@AdultSingle-SOP@Line_15@r1@1516" version="1.0" order="1">
                <Name>East Midlands Airport</Name>
            </FareTableRow>
            """,
            FareTableRow(
                id="Trip@AdultSingle-SOP@Line_15@r1@1516",
                version="1.0",
                order="1",
                Name=MultilingualString(
                    value="East Midlands Airport", lang=None, textIdType=None
                ),
            ),
            id="Basic fare table row",
        ),
        pytest.param(
            """
            <FareTableRow id="Trip@AdultSingle-SOP@Line_15@r2@1517" version="1.1" order="2">
                <Name>Long Eaton</Name>
            </FareTableRow>
            """,
            FareTableRow(
                id="Trip@AdultSingle-SOP@Line_15@r2@1517",
                version="1.1",
                order="2",
                Name=MultilingualString(value="Long Eaton", lang=None, textIdType=None),
            ),
            id="Another fare table row",
        ),
        pytest.param(
            """
            <FareTableRow id="Trip@AdultSingle-SOP@Line_15@r1@1516" version="1.0" order="1">
                <Name>East Midlands Airport</Name>
                <UnknownTag>Some content</UnknownTag>
            </FareTableRow>
            """,
            FareTableRow(
                id="Trip@AdultSingle-SOP@Line_15@r1@1516",
                version="1.0",
                order="1",
                Name=MultilingualString(
                    value="East Midlands Airport", lang=None, textIdType=None
                ),
            ),
            id="Row with unknown tag",
        ),
    ],
)
def test_parse_fare_table_row(xml_str: str, expected: FareTableRow) -> None:
    """Test parsing of fare table row with various valid inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_fare_table_row(elem)
    assert result is not None
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str",
    [
        pytest.param(
            """
            <FareTableRow id="Trip@AdultSingle-SOP@Line_15@r1@1516" version="1.0">
                <Name>East Midlands Airport</Name>
            </FareTableRow>
            """,
            id="Row missing order",
        ),
        pytest.param(
            """
            <FareTableRow id="Trip@AdultSingle-SOP@Line_15@r1@1516" version="1.0" order="1">
            </FareTableRow>
            """,
            id="Row missing name",
        ),
        pytest.param(
            """
            <FareTableRow version="1.0" order="1">
                <Name>East Midlands Airport</Name>
            </FareTableRow>
            """,
            id="Row missing id",
        ),
    ],
)
def test_parse_fare_table_row_errors(xml_str: str) -> None:
    """Test parsing of fare table row with invalid inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_fare_table_row(elem)
    assert result is None
