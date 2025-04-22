"""
ServiceFrame Parsing Helpers
"""

from structlog.stdlib import get_logger

from ..models import Line, ServiceFrame

log = get_logger()


def get_lines_from_service_frames(frames: list[ServiceFrame]) -> list[Line]:
    """
    Get a list of lines across as list of service frames
    """
    return [line for frame in frames for line in frame.lines]


def get_line_ids_from_service_frames(frames: list[ServiceFrame]) -> list[str]:
    """
    Get Line Ids from a list of service frames
    """
    return [line.id for frame in frames for line in frame.lines]


def get_line_public_codes_from_service_frames(frames: list[ServiceFrame]) -> list[str]:
    """
    Get Line Public Codes
    """
    return [
        line.PublicCode for frame in frames for line in frame.lines if line.PublicCode
    ]


def get_atco_area_codes_from_service_frames(frames: list[ServiceFrame]) -> list[int]:
    """
    Get the list of three digit Atco Area Cdes from Scheduled StopPoints
    This is the first three digits of the Atco Codes
    """
    area_codes: set[int] = set()

    for frame in frames:
        for stop_point in frame.scheduledStopPoints:
            area_code = stop_point.atco_area_code
            if area_code and area_code.isdigit():
                area_codes.add(int(area_code))
    log.debug("Atco Area Codes found", area_codes=area_codes)
    return list(area_codes)
