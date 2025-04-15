"""
Time Calculation Utils
"""

from datetime import UTC, datetime

from dateutil import parser


def to_days(_, days: int, *_args: tuple[str]) -> float:
    """Returns number of days as number of seconds."""
    return days * 24 * 60 * 60.0


def today(_) -> float:
    """
    Gets current UTC date as a Unix timestamp
    """
    now = datetime.now(UTC).date().isoformat()
    date = parser.parse(now)
    return date.timestamp()
