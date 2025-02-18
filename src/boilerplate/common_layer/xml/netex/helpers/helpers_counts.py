"""
Various Counts
"""

from pydantic import BaseModel

from ..models import CompositeFrame, FareFrame, ResourceFrame, ServiceFrame
from .helpers_fare_frame_zones import get_fare_zones
from .helpers_service_frame import get_lines_from_service_frames


class SortedFrames(BaseModel):
    """
    Sorted Frames
    """

    service_frames: list[ServiceFrame] = []
    resource_frames: list[ResourceFrame] = []
    fare_frames: list[FareFrame] = []


def sort_frames(
    frames: list[CompositeFrame | ResourceFrame | ServiceFrame | FareFrame],
) -> SortedFrames:
    """
    Sorts frames into their respective types using pattern matching. Handles both top-level frames
    and frames nested within CompositeFrames.
    """
    sorted_frames = SortedFrames()
    frames_to_process = list(frames)

    while frames_to_process:
        frame = frames_to_process.pop()
        match frame:
            case CompositeFrame():
                frames_to_process.extend(frame.frames)
            case ServiceFrame():
                sorted_frames.service_frames.append(frame)
            case ResourceFrame():
                sorted_frames.resource_frames.append(frame)
            case FareFrame():
                sorted_frames.fare_frames.append(frame)

    return sorted_frames


def number_of_lines(frames: list[ServiceFrame]) -> int:
    """
    Number of Lines in a Netex Doc
    """
    lines = get_lines_from_service_frames(frames)
    return len(lines)


def number_of_fare_zones(frames: list[FareFrame]) -> int:
    """
    Number of Fare Zones
    """
    return len(get_fare_zones(frames))
