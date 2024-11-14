"""
Functions to generate lists of data
"""

import datetime

from structlog.stdlib import get_logger

from timetables_etl.app.txc.models.txc_service import TXCService

log = get_logger()


def get_line_names(services: list[TXCService]) -> list[str]:
    """
    Get a list of line names from a TXC's Services
    """
    line_names: list[str] = []
    for service in services:
        for line in service.Lines:
            line_names.append(line.LineName)
    return line_names


def parse_departure_time(time_str: str) -> datetime.time | None:
    """
    Parse TXC Departure time into a datetime.time
    """
    try:
        hour, minute, second = map(int, time_str.split(":"))
        departure_time = datetime.time(hour, minute, second)
    except ValueError:
        log.error("Error parsing departure time", time_str=time_str)
        return None
    return departure_time
