"""
Handling Journey Durations and WaitTimes
"""

import re
from datetime import timedelta

from common_layer.xml.txc.models import (
    TXCFlexibleVehicleJourney,
    TXCJourneyPatternTimingLink,
    TXCVehicleJourney,
)
from structlog.stdlib import get_logger

from .models_context import LinkContext

log = get_logger()


def parse_duration(duration: str | None) -> timedelta:
    """Convert ISO 8601 duration to timedelta, returns 0 if None"""
    if not duration:
        return timedelta(0)

    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return timedelta(0)

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def determine_wait_time(
    current_link: TXCJourneyPatternTimingLink,
    next_link: TXCJourneyPatternTimingLink | None,
    is_first_stop: bool,
    is_last_stop: bool,
) -> str | None:
    """
    Determine which WaitTime to use based on the custom implementation rules:

    1. Add WaitTime either from the From or the To depending on where it is present
    2. If both From and To are present, pick the <To> WaitTime
    3. The first stop will always take the <From> WaitTime
        (there cannot be a <To> WaitTime for the first stop)
    4. The last stop will not take the <To> WaitTime
        (there cannot be a <From> WaitTime for the last stop)
    5. If one waittime is <WaitTime>PT0S</WaitTime> we consider that not present


    Returns:
        The WaitTime to use (string format like 'PT20M') or None if no wait time should be applied
    """
    # For the first stop, we only care about the From WaitTime of the current link
    if is_first_stop:
        from_wait = current_link.From.WaitTime
        return None if from_wait == "PT0S" else from_wait

    # For the last stop, we don't apply any wait time (we capture arrival time only)
    if is_last_stop:
        return None

    # For intermediate stops, we need to look at the To element of current link
    # and the From element of the next link
    to_wait = current_link.To.WaitTime if current_link.To else None
    from_wait = next_link.From.WaitTime if next_link and next_link.From else None

    # Treat PT0S as not present
    if to_wait == "PT0S":
        to_wait = None
    if from_wait == "PT0S":
        from_wait = None

    # If both are present, prioritize the To WaitTime
    if to_wait is not None:
        return to_wait

    # Otherwise, use the From WaitTime of the next link if it exists
    return from_wait


def get_pattern_timing(
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
    link_id: str,
    base_link_runtime: str,
    link_context: LinkContext,
) -> tuple[timedelta, timedelta]:
    """
    Get runtime and wait time, handling both vehicle journey types

    Returns:
        A tuple of (runtime, wait_time) as timedelta objects
    """
    runtime = parse_duration(base_link_runtime)

    # For regular vehicle journeys, check for timing overrides
    if isinstance(txc_vehicle_journey, TXCVehicleJourney):
        for vj_link in txc_vehicle_journey.VehicleJourneyTimingLink:
            if vj_link.JourneyPatternTimingLinkRef == link_id:
                runtime = parse_duration(vj_link.RunTime)
                break
        else:
            if txc_vehicle_journey.VehicleJourneyTimingLink:
                log.warning(
                    "Missing timing link in vehicle journey - using base runtime",
                    vehicle_journey_id=txc_vehicle_journey.VehicleJourneyCode,
                    requested_link=link_id,
                    available_links=[
                        vl.JourneyPatternTimingLinkRef
                        for vl in txc_vehicle_journey.VehicleJourneyTimingLink
                    ],
                )

    wait_time_str = determine_wait_time(
        current_link=link_context.current_link,
        next_link=link_context.next_link,
        is_first_stop=link_context.is_first_stop,
        is_last_stop=link_context.is_last_stop,
    )
    wait_time = parse_duration(wait_time_str)

    return runtime, wait_time
