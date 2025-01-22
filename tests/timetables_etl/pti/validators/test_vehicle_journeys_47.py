"""
Test Vehicle Journeys Observation 47
Mandatory elements incorrect in Destination Display
"""

import pytest

from tests.timetables_etl.pti.validators.test_vehicle_journeys_39 import DATA_DIR

from .conftest import run_validation

OBSERVATION_ID = 47


@pytest.mark.parametrize(
    "filename, expected",
    [
        pytest.param(
            "destinationdisplayjourneypattern.xml",
            True,
            id="Valid Journey Pattern Destination Display",
        ),
        pytest.param(
            "dynamicdisplaytiminglinks.xml",
            True,
            id="Valid Dynamic Display Timing Links",
        ),
        pytest.param(
            "dynamicdisplaytiminglinksfail.xml",
            False,
            id="Invalid Dynamic Display Timing Links",
        ),
    ],
)
def test_destination_display(filename: str, expected: bool):
    """Test validation of destination display elements in vehicle journeys"""
    is_valid = run_validation(filename, DATA_DIR, OBSERVATION_ID)
    assert is_valid == expected
