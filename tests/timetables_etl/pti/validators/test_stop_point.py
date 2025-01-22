"""
StopPoint PTI Checks
"""

from pathlib import Path

import pytest
from lxml import etree
from pti.app.validators.functions import validate_non_naptan_stop_points

from tests.timetables_etl.pti.validators.conftest import run_validation

DATA_DIR = Path(__file__).parent / "data" / "stop_points"
NAMESPACE = {"x": "http://www.transxchange.org.uk/"}

OBSERVATION_ID = 28


@pytest.mark.parametrize(
    "filename, expected",
    [
        pytest.param("bodp3615stoppoints.xml", True, id="Valid Stop Points"),
        pytest.param(
            "bodp3615stoppointsfail2month.xml", False, id="Invalid Two Months Duration"
        ),
        pytest.param(
            "bodp3615stoppointsfailnodate.xml", False, id="Invalid Missing Date"
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
    """Test validation of non-NaPTAN stop points in TXC files"""
    is_valid = run_validation(filename, DATA_DIR, OBSERVATION_ID)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("stop_point_missing_mode.xml", False),
        ("stop_point_w_bus_mode.xml", False),
        ("stop_point_w_coach_mode.xml", True),
        ("stop_point_w_bus_mode_success.xml", True),
        ("stop_point_w_bus_mode_blank_enddate.xml", True),
        ("stop_point_w_bus_mode_wo_operating_profile.xml", True),
    ],
)
def test_check_stop_point_two_months(filename, expected):

    string_xml = DATA_DIR / filename
    with string_xml.open("r") as txc_xml:
        doc = etree.parse(txc_xml)
        elements = doc.xpath("//x:StopPoint", namespaces=NAMESPACE)
        actual = validate_non_naptan_stop_points("", elements)
        assert actual == expected
