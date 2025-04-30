"""
Time Duration Parsing
"""

import re
from datetime import timedelta

DURATION_PATTERN = re.compile(
    r"(-)?P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?"
)


def parse_duration(duration: str | None) -> timedelta:
    """
    Convert ISO 8601 duration to timedelta, returns 0 if None
    Handles negative durations, decimal seconds, and days
    """
    if not duration:
        return timedelta(0)

    match = DURATION_PATTERN.match(duration)
    if not match:
        return timedelta(0)

    sign = -1 if match.group(1) else 1
    days = int(match.group(2) or 0)
    hours = int(match.group(3) or 0)
    minutes = int(match.group(4) or 0)

    seconds_str = match.group(5) or "0"
    seconds_float = float(seconds_str)
    seconds = int(seconds_float)
    microseconds = int((seconds_float - seconds) * 1_000_000)

    return sign * timedelta(
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        microseconds=microseconds,
    )
