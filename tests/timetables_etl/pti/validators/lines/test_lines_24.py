"""
Test Services Observation 24
Mandatory elements incorrect for Line ID.
"""

import pytest

from tests.timetables_etl.pti.validators.conftest import run_validation

from .conftest import DATA_DIR

OBSERVATION_ID = 24


@pytest.mark.parametrize(
    "filename, expected",
    [
        pytest.param("bodp3613lineidfail.xml", False, id="Invalid Line ID Format"),
        pytest.param(
            "bodp3613lineidfailspaces.xml", False, id="Invalid Line ID With Spaces"
        ),
        pytest.param("bodp3613lineidpass.xml", True, id="Valid Line ID Format"),
    ],
)
def test_line_id_format(filename: str, expected: bool):
    """Test validation of line ID format and characters"""
    is_valid = run_validation(filename, DATA_DIR, OBSERVATION_ID)
    assert is_valid == expected
