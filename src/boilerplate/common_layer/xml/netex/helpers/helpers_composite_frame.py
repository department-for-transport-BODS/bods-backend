"""
CompositeFrame Helper Functions
"""

from datetime import datetime

from common_layer.xml.netex.parser.netex_constants import (
    NETEX_METADATA_FRAME_IDENTIFIER,
)
from structlog.stdlib import get_logger

from ..models import CompositeFrame

log = get_logger()


def filter_non_metadata_frames(frames: list[CompositeFrame]) -> list[CompositeFrame]:
    """
    Filter out UK PI Metadata frames from the input frames.
    TODO: Explain why this is done in the docstring
    """
    if not frames:
        log.debug("No Frames Provided", count=0)
        return []

    filtered_frames = [
        frame for frame in frames if NETEX_METADATA_FRAME_IDENTIFIER not in frame.id
    ]

    if not filtered_frames:
        log.debug("Only UK Metadata Frames Found", originalCount=len(frames))

    return filtered_frames


def get_composite_frame_valid_from(frames: list[CompositeFrame]) -> datetime | None:
    """
    Get the earliest valid from date from a list of composite frames.
    Excludes UK PI Metadata frames from consideration.
    Returns None if no valid frames remain after filtering.
    """
    filtered_frames = filter_non_metadata_frames(frames)
    if not filtered_frames:
        return None

    valid_from_dates = [
        frame.ValidBetween.FromDate
        for frame in filtered_frames
        if frame.ValidBetween and frame.ValidBetween.FromDate
    ]

    if not valid_from_dates:
        log.debug("No Valid From Dates Found", frameCount=len(filtered_frames))
        return None

    earliest_date = min(valid_from_dates)

    if len(valid_from_dates) > 1:
        log.debug(
            "Multiple Valid From Dates Found",
            frameCount=len(filtered_frames),
            dateCount=len(valid_from_dates),
            earliestDate=earliest_date,
            allDates=valid_from_dates,
        )
    else:
        log.debug(
            "Valid From Date Found", frameCount=len(filtered_frames), date=earliest_date
        )

    return earliest_date


def get_composite_frame_valid_to(frames: list[CompositeFrame]) -> datetime | None:
    """
    Get the latest valid to date from a list of composite frames.
    Excludes UK PI Metadata frames from consideration.
    Returns None if no valid frames remain after filtering.
    """
    filtered_frames = filter_non_metadata_frames(frames)
    if not filtered_frames:
        return None

    valid_to_dates = [
        frame.ValidBetween.ToDate
        for frame in filtered_frames
        if frame.ValidBetween and frame.ValidBetween.ToDate
    ]

    if not valid_to_dates:
        log.debug("No Valid To Dates Found", frameCount=len(filtered_frames))
        return None

    latest_date = max(valid_to_dates)

    if len(valid_to_dates) > 1:
        log.debug(
            "Multiple Valid To Dates Found",
            frameCount=len(filtered_frames),
            dateCount=len(valid_to_dates),
            latestDate=latest_date,
            allDates=valid_to_dates,
        )
    else:
        log.debug(
            "Valid To Date Found", frameCount=len(filtered_frames), date=latest_date
        )

    return latest_date
