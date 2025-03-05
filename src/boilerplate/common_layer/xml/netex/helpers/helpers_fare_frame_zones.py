"""
FareZone Helpers
"""

from common_layer.xml.netex.models.netex_references import ScheduledStopPointReference

from ..models import FareFrame, FareZone


def get_fare_zones(frames: list[FareFrame]) -> list[FareZone]:
    """
    Get a list of lines across as list of service frames
    """

    return [zone for frame in frames if frame.fareZones for zone in frame.fareZones]


def get_scheduled_stop_point_refs(
    frames: list[FareFrame],
) -> list[ScheduledStopPointReference]:
    """
    Get a list of ScheduledStopPointRefs across all Fare Frames
    """

    fare_zones = get_fare_zones(frames)

    members = [stop.members for stop in fare_zones if stop.members is not None]

    stops = [
        stop_ref
        for member in members
        if member.ScheduledStopPointRef
        for stop_ref in member.ScheduledStopPointRef
    ]

    return stops
