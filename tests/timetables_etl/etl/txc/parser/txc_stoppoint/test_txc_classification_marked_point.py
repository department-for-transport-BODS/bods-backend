"""
Test MarkedPoint
"""

import pytest
from common_layer.txc.models.txc_stoppoint import UnmarkedPointStructure
from common_layer.txc.models.txc_stoppoint.stop_point_marked import (
    BearingStructure,
    MarkedPointStructure,
)
from common_layer.txc.parser.stop_points import (
    parse_bearing_structure,
    parse_marked_point_structure,
)
from common_layer.txc.parser.stop_points.parse_stop_point_classification import (
    parse_unmarked_point_structure,
)
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "bearing_xml_str, expected_result",
    [
        pytest.param(
            "<Bearing><CompassPoint>N</CompassPoint></Bearing>",
            BearingStructure(CompassPoint="N"),
            id="Valid BearingStructure",
        ),
        pytest.param(
            "<Bearing></Bearing>",
            None,
            id="Missing CompassPoint",
        ),
        pytest.param(
            "<Bearing><CompassPoint>InvalidPoint</CompassPoint></Bearing>",
            None,
            id="nvalid CompassPoint",
        ),
    ],
)
def test_parse_bearing_structure(
    bearing_xml_str: str, expected_result: BearingStructure | None
):
    """
    Parsing of Bus Stop Structure
    """
    bearing_xml = fromstring(bearing_xml_str)
    assert parse_bearing_structure(bearing_xml) == expected_result


@pytest.mark.parametrize(
    "marked_point_xml_str, expected_result",
    [
        pytest.param(
            """
            <MarkedPoint>
                <Bearing>
                    <CompassPoint>N</CompassPoint>
                </Bearing>
            </MarkedPoint>
            """,
            MarkedPointStructure(Bearing=BearingStructure(CompassPoint="N")),
            id="Valid MarkedPointStructure",
        ),
        pytest.param(
            "<MarkedPoint></MarkedPoint>",
            None,
            id="Missing Bearing",
        ),
        pytest.param(
            """
            <MarkedPoint>
                <Bearing>
                    <CompassPoint>InvalidPoint</CompassPoint>
                </Bearing>
            </MarkedPoint>
            """,
            None,
            id="Invalid Bearing",
        ),
    ],
)
def test_parse_marked_point_structure(
    marked_point_xml_str: str, expected_result: MarkedPointStructure | None
):
    """
    Test Parsing a Marked Point Structure
    """
    marked_point_xml = fromstring(marked_point_xml_str)
    assert parse_marked_point_structure(marked_point_xml) == expected_result


@pytest.mark.parametrize(
    "unmarked_point_xml_str, expected_result",
    [
        pytest.param(
            """
            <UnmarkedPoint>
                <Bearing>
                    <CompassPoint>N</CompassPoint>
                </Bearing>
            </UnmarkedPoint>
            """,
            UnmarkedPointStructure(Bearing=BearingStructure(CompassPoint="N")),
            id="Valid UnmarkedPointStructure",
        ),
        pytest.param(
            "<UnmarkedPoint></UnmarkedPoint>",
            None,
            id="Missing Bearing",
        ),
        pytest.param(
            """
            <UnmarkedPoint>
                <Bearing>
                    <CompassPoint>InvalidPoint</CompassPoint>
                </Bearing>
            </UnmarkedPoint>
            """,
            None,
            id="Invalid Bearing",
        ),
    ],
)
def test_parse_unmarked_point_structure(
    unmarked_point_xml_str: str, expected_result: UnmarkedPointStructure | None
):
    """
    Test Parsing an Unmarked Point Structure
    """
    unmarked_point_xml = fromstring(unmarked_point_xml_str)
    assert parse_unmarked_point_structure(unmarked_point_xml) == expected_result
