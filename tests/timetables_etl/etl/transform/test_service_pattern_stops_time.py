"""
Tests For time based functions
"""

from datetime import time, timedelta

import pytest

from timetables_etl.etl.app.transform.service_pattern_stops import (
    calculate_next_time,
    parse_time,
)


@pytest.mark.parametrize(
    "time_value,expected",
    [
        pytest.param(
            "13:45:00",
            time(13, 45),
            id="Valid time string",
        ),
        pytest.param(
            time(14, 30),
            time(14, 30),
            id="Already time object",
        ),
        pytest.param(
            None,
            None,
            id="None returns None",
        ),
        pytest.param(
            "25:00:00",
            None,
            id="Invalid time returns None",
        ),
    ],
)
def test_parse_time(time_value: str | time | None, expected: time | None) -> None:
    """Test parsing of time values"""
    result = parse_time(time_value)
    assert result == expected


@pytest.mark.parametrize(
    "current,runtime,wait,expected",
    [
        pytest.param(
            "09:00:00",
            timedelta(minutes=30),
            timedelta(minutes=5),
            time(9, 35),
            id="Simple addition with wait time",
        ),
        pytest.param(
            time(15, 45),
            timedelta(hours=1),
            timedelta(0),
            time(16, 45),
            id="Hour crossing no wait",
        ),
        pytest.param(
            "23:45:00",
            timedelta(minutes=20),
            timedelta(minutes=10),
            time(0, 15),
            id="Day boundary crossing",
        ),
        pytest.param(
            None,
            timedelta(minutes=10),
            timedelta(0),
            None,
            id="None current time returns None",
        ),
    ],
)
def test_calculate_next_time(
    current: str | time | None,
    runtime: timedelta,
    wait: timedelta,
    expected: time | None,
) -> None:
    """
    Test calculation of next departure time

    """
    result = calculate_next_time(current, runtime, wait)
    assert result == expected
