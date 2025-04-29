"""
Test Duration Parsing
"""

from datetime import timedelta

import pytest
from common_layer.xml.utils import parse_duration


@pytest.mark.parametrize(
    "duration_str,expected",
    [
        pytest.param(
            "PT1H30M",
            timedelta(hours=1, minutes=30),
            id="Hours and minutes",
        ),
        pytest.param(
            "PT45M",
            timedelta(minutes=45),
            id="Minutes only",
        ),
        pytest.param(
            "PT2H",
            timedelta(hours=2),
            id="Hours only",
        ),
        pytest.param(
            "PT1H20M30S",
            timedelta(hours=1, minutes=20, seconds=30),
            id="Hours, minutes and seconds",
        ),
        pytest.param(
            None,
            timedelta(0),
            id="None returns zero duration",
        ),
        pytest.param(
            "invalid",
            timedelta(0),
            id="Invalid format returns zero duration",
        ),
        pytest.param(
            "-PT1H30M",
            timedelta(hours=-1, minutes=-30),
            id="Negative hours and minutes",
        ),
        pytest.param(
            "-PT45M",
            timedelta(minutes=-45),
            id="Negative minutes only",
        ),
        pytest.param(
            "-PT1H20M30S",
            timedelta(hours=-1, minutes=-20, seconds=-30),
            id="Negative hours, minutes and seconds",
        ),
        pytest.param(
            "PT1M30.5S",
            timedelta(minutes=1, seconds=30, microseconds=500000),
            id="Decimal seconds",
        ),
        pytest.param(
            "PT0.5S",
            timedelta(microseconds=500000),
            id="Decimal seconds only",
        ),
        pytest.param(
            "P0D",
            timedelta(0),
            id="Zero days",
        ),
        pytest.param(
            "PT0S",
            timedelta(0),
            id="Zero seconds",
        ),
    ],
)
def test_parse_duration(duration_str: str | None, expected: timedelta) -> None:
    """Test parsing of ISO 8601 duration strings"""
    result = parse_duration(duration_str)
    assert result == expected
