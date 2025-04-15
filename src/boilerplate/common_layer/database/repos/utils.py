"""
Util functions for database repo classes
"""

from datetime import date, datetime


def date_to_datetime(date_obj: date | None) -> datetime | None:
    """
    Convert date to a datetime object with time 00:00:00
    """
    return datetime.combine(date_obj, datetime.min.time()) if date_obj else None
