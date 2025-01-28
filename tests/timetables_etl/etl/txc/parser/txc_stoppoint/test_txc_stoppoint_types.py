"""
Test Stop Point Types Parsing
"""

import pytest
from common_layer.txc.models.txc_stoppoint import FerryStopClassificationStructure
from common_layer.txc.models.txc_stoppoint.stop_point_types import (
    RailStopClassificationStructure,
)
from common_layer.txc.parser.stop_points.parse_stop_point_types import (
    parse_ferry_structure,
    parse_rail_structure,
)
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "ferry_xml_str, expected_result",
    [
        pytest.param(
            """
            <Ferry>
                <Entrance />
            </Ferry>
            """,
            FerryStopClassificationStructure(
                Entrance=True, AccessArea=False, Berth=False
            ),
            id="Ferry Terminal Entrance",
        ),
        pytest.param(
            """
            <Ferry>
                <AccessArea />
            </Ferry>
            """,
            FerryStopClassificationStructure(
                Entrance=False, AccessArea=True, Berth=False
            ),
            id="Ferry Access Area",
        ),
        pytest.param(
            """
            <Ferry>
                <Berth />
            </Ferry>
            """,
            FerryStopClassificationStructure(
                Entrance=False, AccessArea=False, Berth=True
            ),
            id="Ferry Berth",
        ),
        pytest.param(
            """
            <Ferry>
                <Entrance />
                <AccessArea />
                <Berth />
            </Ferry>
            """,
            FerryStopClassificationStructure(
                Entrance=True, AccessArea=True, Berth=True
            ),
            id="Ferry Multiple Elements",
        ),
        pytest.param(
            """
            <Ferry>
            </Ferry>
            """,
            None,
            id="Empty Ferry Element",
        ),
    ],
)
def test_parse_ferry_structure(
    ferry_xml_str: str, expected_result: FerryStopClassificationStructure | None
):
    """
    Ferry Stop Classification Structure Parsing test
    """
    ferry_xml = fromstring(ferry_xml_str)
    assert parse_ferry_structure(ferry_xml) == expected_result


@pytest.mark.parametrize(
    "rail_xml_str, expected_result",
    [
        pytest.param(
            """
            <Rail>
                <Entrance />
            </Rail>
            """,
            RailStopClassificationStructure(
                Entrance=True, AccessArea=False, Platform=False
            ),
            id="Rail Station Entrance",
        ),
        pytest.param(
            """
            <Rail>
                <AccessArea />
            </Rail>
            """,
            RailStopClassificationStructure(
                Entrance=False, AccessArea=True, Platform=False
            ),
            id="Rail Access Area",
        ),
        pytest.param(
            """
            <Rail>
                <Platform />
            </Rail>
            """,
            RailStopClassificationStructure(
                Entrance=False, AccessArea=False, Platform=True
            ),
            id="Rail Platform",
        ),
        pytest.param(
            """
            <Rail>
                <Entrance />
                <AccessArea />
                <Platform />
            </Rail>
            """,
            RailStopClassificationStructure(
                Entrance=True, AccessArea=True, Platform=True
            ),
            id="Rail Multiple Elements",
        ),
        pytest.param(
            """
            <Rail>
            </Rail>
            """,
            None,
            id="Empty Rail Element",
        ),
    ],
)
def test_parse_rail_structure(
    rail_xml_str: str, expected_result: RailStopClassificationStructure | None
):
    """
    Rail Stop Classification Structure Parsing test
    """
    rail_xml = fromstring(rail_xml_str)
    assert parse_rail_structure(rail_xml) == expected_result
