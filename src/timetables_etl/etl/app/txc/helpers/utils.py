"""
Functions to generate lists of data
"""

import datetime

from structlog.stdlib import get_logger

log = get_logger()


def parse_departure_time(time_str: str) -> datetime.time | None:
    """
    Parse TXC Departure time into a datetime.time
    """
    try:
        return datetime.datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        log.error("Error parsing departure time", time_str=time_str)
        return None
