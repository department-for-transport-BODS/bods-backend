"""
Lines PTI Tests
"""

from unittest.mock import patch

import pytest

from tests.timetables_etl.pti.validators.conftest import TXCFile

from ..conftest import create_validator, run_validation
from .conftest import DATA_DIR

OBSERVATION_ID = 23


@pytest.fixture(autouse=True, scope="module", name="mocked_stop_point_repo")
def m_stop_point_repo():
    """
    Patched Stop Point Repo
    """
    with patch("pti.app.validators.functions.NaptanStopPointRepo") as m_repo:
        yield m_repo


def test_validate_less_than_two_lines():
    """Test validation of service with single line"""
    service = """
    <Service>
        <ServiceCode>FIN50</ServiceCode>
        <Lines>
            <Line id="l_1">
                <LineName>A1</LineName>
            </Line>
        </Lines>
    </Service>
    """
    xml = f"<Services>{service}</Services>"

    pti, _ = create_validator("dummy.xml", DATA_DIR, OBSERVATION_ID)
    is_valid = pti.is_valid(TXCFile(xml))
    assert is_valid


@pytest.mark.parametrize(
    "filename, expected",
    [
        pytest.param("nonrelatedlines.xml", False, id="Non Related Lines"),
        pytest.param(
            "relatedlinesbylocalityname.xml", True, id="Related Lines By Locality Name"
        ),
        pytest.param(
            "relatedlinesbyjp.xml", True, id="Related Lines By Journey Pattern"
        ),
        pytest.param("relatedlinesbystops.xml", True, id="Related Lines By Stops"),
    ],
)
def test_related_lines(filename: str, expected: bool):
    """Test validation of related lines in TXC files"""
    is_valid = run_validation(filename, DATA_DIR, OBSERVATION_ID)
    assert is_valid == expected


def test_non_related_with_stop_areas(mocked_stop_point_repo):
    """
    Test validation of non-related lines with matching stop areas
    The following atco codes come from nonrelatedlines.xml one stop in each line
    """
    l1stop = "9990000001"
    l1_n_stop = "9990000026"
    stop_areas_in_common = ["match"]
    mocked_stop_point_repo.return_value.get_stop_area_map.return_value = {
        l1stop: stop_areas_in_common,
        l1_n_stop: stop_areas_in_common,
    }

    is_valid = run_validation("nonrelatedlines.xml", DATA_DIR, OBSERVATION_ID)
    assert is_valid
