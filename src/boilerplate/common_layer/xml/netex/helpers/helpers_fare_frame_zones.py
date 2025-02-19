"""
FareZone Helpers
"""

from ..models import FareFrame, FareZone


def get_fare_zones(frames: list[FareFrame]) -> list[FareZone]:
    """
    Get a list of lines across as list of service frames
    """

    return [zone for frame in frames if frame.fareZones for zone in frame.fareZones]
