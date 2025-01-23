"""
Time Calculation Utils
"""

from datetime import UTC, datetime

from dateutil import parser


def to_days(_context, days: int, *_args) -> float:
    """Returns number of days as number of seconds."""
    return days * 24 * 60 * 60.0


def today(_context) -> float:
    """
    Gets current UTC date as a Unix timestamp
    """
    now = datetime.now(UTC).date().isoformat()
    date = parser.parse(now)
    return date.timestamp()
