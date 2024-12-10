"""
Test TXC Helper Utils
"""

from datetime import time

import pytest

from timetables_etl.etl.app.txc.helpers.utils import parse_departure_time


@pytest.mark.parametrize(
    "time_str, expected_result",
    [
        pytest.param(
            "09:30:00",
            time(9, 30, 0),
            id="Valid time",
        ),
        pytest.param(
            "23:59:59",
            time(23, 59, 59),
            id="End of day time",
        ),
        pytest.param(
            "00:00:00",
            time(0, 0, 0),
            id="Midnight time",
        ),
        pytest.param(
            "25:00:00",
            None,
            id="Invalid hours",
        ),
        pytest.param(
            "12:61:00",
            None,
            id="Invalid minutes",
        ),
        pytest.param(
            "12:30:61",
            None,
            id="Invalid seconds",
        ),
        pytest.param(
            "12:30",
            None,
            id="Missing seconds",
        ),
        pytest.param(
            "invalid",
            None,
            id="Invalid format",
        ),
        pytest.param(
            "",
            None,
            id="Empty string",
        ),
    ],
)
def test_parse_departure_time(time_str: str, expected_result: time | None):
    """
    Test parsing of departure times in HH:MM:SS format
    """
    assert parse_departure_time(time_str) == expected_result
