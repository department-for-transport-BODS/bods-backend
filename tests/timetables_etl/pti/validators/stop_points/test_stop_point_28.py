"""
Test Stop Points Observation 28
Mandatory elements incorrect in 'StopPoint' field.
"""

import pytest
from lxml import etree
from pti.app.constants import NAMESPACE
from pti.app.validators.stop_point import validate_non_naptan_stop_points

from tests.timetables_etl.pti.validators.conftest import run_validation

from .conftest import DATA_DIR

OBSERVATION_ID = 28


@pytest.mark.parametrize(
    "filename, expected",
    [
        pytest.param(
            "bodp3615stoppoints.xml", True, id="Valid Stop Points Within Duration"
        ),
        pytest.param(
            "bodp3615stoppointsfail2month.xml",
            False,
            id="Invalid Stop Points Over Two Months",
        ),
        pytest.param(
            "bodp3615stoppointsfailnodate.xml",
            False,
            id="Invalid Stop Points Missing Date",
        ),
        pytest.param(
            "stoppointsinheritfromservice2months.xml",
            True,
            id="Valid Service Inherited Two Months",
        ),
        pytest.param(
            "stoppointsinheritfromservice2monthsplus.xml",
            False,
            id="Invalid Service Inherited Over Two Months",
        ),
        pytest.param(
            "stoppointsinheritstartdatefromservice.xml",
            True,
            id="Valid Service Inherited Start Date",
        ),
        pytest.param(
            "stoppointsinheritenddatefromservice.xml",
            True,
            id="Valid Service Inherited End Date",
        ),
    ],
)
def test_non_naptan_stop_points(filename: str, expected: bool):
    """Test validation of non-NaPTAN stop points and their validity durations"""
    is_valid = run_validation(filename, DATA_DIR, OBSERVATION_ID)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        pytest.param("stop_point_missing_mode.xml", False, id="Missing Mode"),
        pytest.param("stop_point_w_bus_mode.xml", False, id="Invalid Bus Mode"),
        pytest.param("stop_point_w_coach_mode.xml", True, id="Valid Coach Mode"),
        pytest.param("stop_point_w_bus_mode_success.xml", True, id="Valid Bus Mode"),
        pytest.param(
            "stop_point_w_bus_mode_blank_enddate.xml", True, id="Valid Blank End Date"
        ),
        pytest.param(
            "stop_point_w_bus_mode_wo_operating_profile.xml",
            True,
            id="Valid Without Operating Profile",
        ),
    ],
)
def test_check_stop_point_two_months(filename: str, expected: bool):
    """
    Test stop points with different modes and operating profiles
    Within two month duration
    """
    string_xml = DATA_DIR / filename
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:StopPoint", namespaces=NAMESPACE)
        actual = validate_non_naptan_stop_points(None, elements)
        assert actual == expected
