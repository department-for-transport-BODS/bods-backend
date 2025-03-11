"""
Handling Journey Durations and WaitTimes
"""

import re
from datetime import timedelta

from common_layer.xml.txc.models import (
    TXCFlexibleVehicleJourney,
    TXCJourneyPatternTimingLink,
    TXCVehicleJourney,
    TXCVehicleJourneyTimingLink,
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


def apply_wait_time_rules(
    from_wait: str | None,
    to_wait: str | None,
    next_from_wait: str | None,
    is_first_stop: bool,
    is_last_stop: bool,
) -> str | None:
    """
    Apply the common rules for determining which wait time to use.

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
    # For the first stop, we only care about the From WaitTime
    if is_first_stop:
        return None if from_wait == "PT0S" else from_wait

    # For the last stop, we don't apply any wait time (we capture arrival time only)
    if is_last_stop:
        return None

    # Treat PT0S as not present
    if to_wait == "PT0S":
        to_wait = None
    if next_from_wait == "PT0S":
        next_from_wait = None

    # If both are present, prioritize the To WaitTime
    if to_wait is not None:
        return to_wait

    # Otherwise, use the From WaitTime of the next link if it exists
    return next_from_wait


def determine_wait_time(
    current_link: TXCJourneyPatternTimingLink,
    next_link: TXCJourneyPatternTimingLink | None,
    is_first_stop: bool,
    is_last_stop: bool,
) -> str | None:
    """
    Determine which WaitTime to use for JourneyPatternTimingLink

    Returns:
        The WaitTime to use (string format like 'PT20M') or None if no wait time should be applied
    """
    # Extract wait times from JourneyPatternTimingLink
    from_wait = current_link.From.WaitTime if current_link.From else None
    to_wait = current_link.To.WaitTime if current_link.To else None
    next_from_wait = next_link.From.WaitTime if next_link and next_link.From else None

    return apply_wait_time_rules(
        from_wait, to_wait, next_from_wait, is_first_stop, is_last_stop
    )


def determine_vehicle_journey_wait_time(
    matching_link: TXCVehicleJourneyTimingLink | None,
    next_link: TXCVehicleJourneyTimingLink | None,
    is_first_stop: bool,
    is_last_stop: bool,
) -> str | None:
    """
    Determine wait time from VehicleJourneyTimingLink

    Returns:
        The WaitTime to use (string format like 'PT20M') or None if no wait time should be applied
    """
    if not matching_link:
        return None

    # Extract wait times from VehicleJourneyTimingLink
    from_wait = matching_link.From.WaitTime if matching_link.From else None
    to_wait = matching_link.To.WaitTime if matching_link.To else None
    next_from_wait = next_link.From.WaitTime if next_link and next_link.From else None

    return apply_wait_time_rules(
        from_wait, to_wait, next_from_wait, is_first_stop, is_last_stop
    )


def find_vehicle_journey_timing_links(
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
    link_id: str,
    next_link_id: str | None = None,
) -> tuple[
    TXCVehicleJourneyTimingLink | None, TXCVehicleJourneyTimingLink | None, timedelta
]:
    """
    Find the matching VehicleJourneyTimingLink and possibly the next one.

    Returns:
        tuple: (matching_link, next_link, runtime)
    """
    matching_link: TXCVehicleJourneyTimingLink | None = None
    next_link: TXCVehicleJourneyTimingLink | None = None
    runtime = timedelta(0)  # Default to 0

    if isinstance(txc_vehicle_journey, TXCVehicleJourney):
        vj_links = txc_vehicle_journey.VehicleJourneyTimingLink
        for i, vj_link in enumerate(vj_links):
            if vj_link.JourneyPatternTimingLinkRef == link_id:
                matching_link = vj_link
                runtime = parse_duration(vj_link.RunTime)

                # Try to find the next VJ link if this isn't the last one and we have a next_link_id
                if i < len(vj_links) - 1 and next_link_id:
                    if vj_links[i + 1].JourneyPatternTimingLinkRef == next_link_id:
                        next_link = vj_links[i + 1]
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

    return matching_link, next_link, runtime


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
    # Default runtime from base_link_runtime
    runtime = parse_duration(base_link_runtime)

    # Find matching VehicleJourneyTimingLink and next one if any
    next_link_id = link_context.next_link.id if link_context.next_link else None
    matching_vj_link, next_vj_link, vj_runtime = find_vehicle_journey_timing_links(
        txc_vehicle_journey, link_id, next_link_id
    )

    # Use runtime from VehicleJourneyTimingLink if found
    if matching_vj_link:
        runtime = vj_runtime

    # First try to get wait time from VehicleJourneyTimingLink
    wait_time_str = determine_vehicle_journey_wait_time(
        matching_vj_link,
        next_vj_link,
        link_context.is_first_stop,
        link_context.is_last_stop,
    )

    # If no wait time found in VehicleJourneyTimingLink, fall back to JourneyPatternTimingLink
    if wait_time_str is None:
        wait_time_str = determine_wait_time(
            current_link=link_context.current_link,
            next_link=link_context.next_link,
            is_first_stop=link_context.is_first_stop,
            is_last_stop=link_context.is_last_stop,
        )

    wait_time = parse_duration(wait_time_str)
    return runtime, wait_time
