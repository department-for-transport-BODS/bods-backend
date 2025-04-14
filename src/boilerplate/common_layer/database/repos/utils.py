from datetime import date, datetime


def date_to_datetime(date: date | None) -> datetime | None:
    """
    Convert a date to a datetime object with time 00:00:00
    """
    return datetime.combine(date, datetime.min.time()) if date else None
