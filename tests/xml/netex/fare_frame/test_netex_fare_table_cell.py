"""
Test Cell Parsing
"""

import pytest
from common_layer.xml.netex.models import VersionedRef
from common_layer.xml.netex.models.fare_frame.netex_fare_table import (
    Cell,
    DistanceMatrixElementPrice,
)
from common_layer.xml.netex.parser import (
    parse_cell,
    parse_distance_matrix_element_price,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <DistanceMatrixElementPrice version="1.0" id="Trip@AdultSingle-SOP@Line_15@1502+1503">
                <GeographicalIntervalPriceRef version="1.0" ref="price_band_2.7@AdultSingle" />
                <DistanceMatrixElementRef version="1.0" ref="1502+1503" />
            </DistanceMatrixElementPrice>
            """,
            DistanceMatrixElementPrice(
                id="Trip@AdultSingle-SOP@Line_15@1502+1503",
                version="1.0",
                GeographicalIntervalPriceRef=VersionedRef(
                    version="1.0", ref="price_band_2.7@AdultSingle"
                ),
                DistanceMatrixElementRef=VersionedRef(version="1.0", ref="1502+1503"),
            ),
            id="Basic distance matrix element price",
        ),
        pytest.param(
            """
            <DistanceMatrixElementPrice version="1.1" id="Trip@AdultSingle-SOP@Line_16@1504+1505">
                <GeographicalIntervalPriceRef version="1.1" ref="price_band_3.0@AdultSingle" />
                <DistanceMatrixElementRef version="1.1" ref="1504+1505" />
                <UnknownTag>Some content</UnknownTag>
            </DistanceMatrixElementPrice>
            """,
            DistanceMatrixElementPrice(
                id="Trip@AdultSingle-SOP@Line_16@1504+1505",
                version="1.1",
                GeographicalIntervalPriceRef=VersionedRef(
                    version="1.1", ref="price_band_3.0@AdultSingle"
                ),
                DistanceMatrixElementRef=VersionedRef(version="1.1", ref="1504+1505"),
            ),
            id="Price with unknown tag",
        ),
    ],
)
def test_parse_distance_matrix_element_price(
    xml_str: str, expected: DistanceMatrixElementPrice
) -> None:
    """Test parsing of distance matrix element price with various valid inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_distance_matrix_element_price(elem)
    assert result is not None
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str",
    [
        pytest.param(
            """
            <DistanceMatrixElementPrice id="Trip@AdultSingle-SOP@Line_15@1502+1503">
                <GeographicalIntervalPriceRef version="1.0" ref="price_band_2.7@AdultSingle" />
                <DistanceMatrixElementRef version="1.0" ref="1502+1503" />
            </DistanceMatrixElementPrice>
            """,
            id="Price missing version",
        ),
        pytest.param(
            """
            <DistanceMatrixElementPrice version="1.0">
                <GeographicalIntervalPriceRef version="1.0" ref="price_band_2.7@AdultSingle" />
                <DistanceMatrixElementRef version="1.0" ref="1502+1503" />
            </DistanceMatrixElementPrice>
            """,
            id="Price missing id",
        ),
    ],
)
def test_parse_distance_matrix_element_price_errors(xml_str: str) -> None:
    """Test parsing of distance matrix element price with invalid inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_distance_matrix_element_price(elem)
    assert result is None


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """<Cell id="Trip@AdultSingle-SOP@Line_15@1502" version="1.0" order="1">
                <DistanceMatrixElementPrice version="1.0" id="Trip@AdultSingle-SOP@Line_15@1502+1503">
                    <GeographicalIntervalPriceRef version="1.0" ref="price_band_2.7@AdultSingle" />
                    <DistanceMatrixElementRef version="1.0" ref="1502+1503" />
                </DistanceMatrixElementPrice>
                <ColumnRef versionRef="1.0" ref="Trip@AdultSingle-SOP@Line_15@c2@1502" />
                <RowRef versionRef="1.0" ref="Trip@AdultSingle-SOP@Line_15@r13@1503" />
            </Cell>""".strip(),
            Cell(
                id="Trip@AdultSingle-SOP@Line_15@1502",
                version="1.0",
                order="1",
                DistanceMatrixElementPrice=DistanceMatrixElementPrice(
                    id="Trip@AdultSingle-SOP@Line_15@1502+1503",
                    version="1.0",
                    GeographicalIntervalPriceRef=VersionedRef(
                        version="1.0", ref="price_band_2.7@AdultSingle"
                    ),
                    DistanceMatrixElementRef=VersionedRef(
                        version="1.0", ref="1502+1503"
                    ),
                ),
                ColumnRef=VersionedRef(
                    version="1.0", ref="Trip@AdultSingle-SOP@Line_15@c2@1502"
                ),
                RowRef=VersionedRef(
                    version="1.0", ref="Trip@AdultSingle-SOP@Line_15@r13@1503"
                ),
            ),
            id="Basic cell with full details",
        ),
        pytest.param(
            """<Cell id="Trip@AdultSingle-SOP@Line_16@1503" version="1.1" order="2">
                <DistanceMatrixElementPrice version="1.1" id="Trip@AdultSingle-SOP@Line_16@1503+1504">
                    <GeographicalIntervalPriceRef version="1.1" ref="price_band_3.0@AdultSingle" />
                    <DistanceMatrixElementRef version="1.1" ref="1503+1504" />
                    <UnknownTag>Some content</UnknownTag>
                </DistanceMatrixElementPrice>
                <ColumnRef versionRef="1.1" ref="Trip@AdultSingle-SOP@Line_16@c3@1503" />
                <RowRef versionRef="1.1" ref="Trip@AdultSingle-SOP@Line_16@r14@1504" />
            </Cell>""".strip(),
            Cell(
                id="Trip@AdultSingle-SOP@Line_16@1503",
                version="1.1",
                order="2",
                DistanceMatrixElementPrice=DistanceMatrixElementPrice(
                    id="Trip@AdultSingle-SOP@Line_16@1503+1504",
                    version="1.1",
                    GeographicalIntervalPriceRef=VersionedRef(
                        version="1.1", ref="price_band_3.0@AdultSingle"
                    ),
                    DistanceMatrixElementRef=VersionedRef(
                        version="1.1", ref="1503+1504"
                    ),
                ),
                ColumnRef=VersionedRef(
                    version="1.1", ref="Trip@AdultSingle-SOP@Line_16@c3@1503"
                ),
                RowRef=VersionedRef(
                    version="1.1", ref="Trip@AdultSingle-SOP@Line_16@r14@1504"
                ),
            ),
            id="Cell with unknown tag in price",
        ),
    ],
)
def test_parse_cell(xml_str: str, expected: Cell) -> None:
    """Test parsing of cell with various valid inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_cell(elem)
    assert result is not None
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str",
    [
        pytest.param(
            """<Cell id="Trip@AdultSingle-SOP@Line_15@1502" version="1.0">
                <DistanceMatrixElementPrice version="1.0" id="Trip@AdultSingle-SOP@Line_15@1502+1503">
                    <GeographicalIntervalPriceRef version="1.0" ref="price_band_2.7@AdultSingle" />
                    <DistanceMatrixElementRef version="1.0" ref="1502+1503" />
                </DistanceMatrixElementPrice>
                <ColumnRef versionRef="1.0" ref="Trip@AdultSingle-SOP@Line_15@c2@1502" />
                <RowRef versionRef="1.0" ref="Trip@AdultSingle-SOP@Line_15@r13@1503" />
            </Cell>""".strip(),
            id="Cell missing order",
        ),
        pytest.param(
            """<Cell version="1.0" order="1">
                <DistanceMatrixElementPrice version="1.0" id="Trip@AdultSingle-SOP@Line_15@1502+1503">
                    <GeographicalIntervalPriceRef version="1.0" ref="price_band_2.7@AdultSingle" />
                    <DistanceMatrixElementRef version="1.0" ref="1502+1503" />
                </DistanceMatrixElementPrice>
                <ColumnRef versionRef="1.0" ref="Trip@AdultSingle-SOP@Line_15@c2@1502" />
                <RowRef versionRef="1.0" ref="Trip@AdultSingle-SOP@Line_15@r13@1503" />
            </Cell>""".strip(),
            id="Cell missing id",
        ),
        pytest.param(
            """<Cell id="Trip@AdultSingle-SOP@Line_15@1502" version="1.0" order="1">
                <ColumnRef versionRef="1.0" ref="Trip@AdultSingle-SOP@Line_15@c2@1502" />
                <RowRef versionRef="1.0" ref="Trip@AdultSingle-SOP@Line_15@r13@1503" />
            </Cell>""".strip(),
            id="Cell missing DistanceMatrixElementPrice",
        ),
    ],
)
def test_parse_cell_errors(xml_str: str) -> None:
    """Test parsing of cell with invalid inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_cell(elem)
    assert result is None
