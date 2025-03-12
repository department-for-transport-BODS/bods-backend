"""
Test Service Pattern Stop Wait Time / Duration Calculations
"""

import pytest

from timetables_etl.etl.app.transform.service_pattern_stops_durations import (
    apply_wait_time_rules,
)


@pytest.mark.parametrize(
    "from_wait,to_wait,next_from_wait,is_first_stop,is_last_stop,expected",
    [
        pytest.param(
            "PT5M0S",
            None,
            None,
            True,
            False,
            "PT5M0S",
            id="First stop uses From.WaitTime",
        ),
        pytest.param(
            "PT0S",
            None,
            None,
            True,
            False,
            None,
            id="First stop with PT0S returns None",
        ),
        pytest.param(
            "PT5M0S",
            "PT10M0S",
            "PT3M0S",
            False,
            False,
            "PT10M0S",
            id="Intermediate stop prioritizes To.WaitTime",
        ),
        pytest.param(
            None,
            "PT10M0S",
            "PT3M0S",
            False,
            False,
            "PT10M0S",
            id="Intermediate stop with no From.WaitTime uses To.WaitTime",
        ),
        pytest.param(
            None,
            None,
            "PT3M0S",
            False,
            False,
            "PT3M0S",
            id="Intermediate stop with no To.WaitTime uses next From.WaitTime",
        ),
        pytest.param(
            None,
            "PT0S",
            "PT3M0S",
            False,
            False,
            "PT3M0S",
            id="PT0S in To.WaitTime is treated as not present",
        ),
        pytest.param(
            None,
            None,
            "PT0S",
            False,
            False,
            None,
            id="PT0S in next From.WaitTime is treated as not present",
        ),
        pytest.param(
            "PT5M0S",
            "PT10M0S",
            "PT3M0S",
            False,
            True,
            None,
            id="Last stop always returns None",
        ),
        pytest.param(
            None,
            None,
            None,
            False,
            False,
            None,
            id="No wait times available returns None",
        ),
    ],
)
def test_apply_wait_time_rules(
    from_wait: str | None,
    to_wait: str | None,
    next_from_wait: str | None,
    is_first_stop: bool,
    is_last_stop: bool,
    expected: str | None,
) -> None:
    """
    Test that wait time rules are correctly applied for different scenarios.
    """
    result = apply_wait_time_rules(
        from_wait, to_wait, next_from_wait, is_first_stop, is_last_stop
    )
    assert result == expected
