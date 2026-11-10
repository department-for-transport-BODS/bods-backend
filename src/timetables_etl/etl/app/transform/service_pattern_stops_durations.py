"""
Handling Journey Durations and WaitTimes
"""

from datetime import timedelta

from common_layer.xml.txc.models import (
    TXCFlexibleVehicleJourney,
    TXCJourneyPatternTimingLink,
    TXCVehicleJourney,
    TXCVehicleJourneyTimingLink,
)
from common_layer.xml.utils import parse_duration
from structlog.stdlib import get_logger

from .models_context import LinkContext

log = get_logger()


def apply_wait_time_rules(
    from_wait: str | None,
    to_wait: str | None,
    is_first_stop: bool,
    is_last_stop: bool,
) -> str | None:
    """
    Apply the common rules for determining which wait time to use.

    1. Resolve outgoing From and incoming To WaitTime for the same stop
    2. If both From and To are present, pick the <To> WaitTime
    3. The first stop will always take the <From> WaitTime
        (there cannot be a <To> WaitTime for the first stop)
    4. The last stop will not take the <To> WaitTime
        (there cannot be a <From> WaitTime for the last stop)
    5. If one waittime is <WaitTime>PT0S</WaitTime> we consider that not present

    Returns:
        The WaitTime to use (string format like 'PT20M') or None if no wait time should be applied
    """
    if from_wait is not None and parse_duration(from_wait) == timedelta(0):
        from_wait = None
    if to_wait is not None and parse_duration(to_wait) == timedelta(0):
        to_wait = None

    # For the first stop, we only care about the From WaitTime
    if is_first_stop:
        return from_wait

    # For the last stop, we don't apply any wait time (we capture arrival time only)
    if is_last_stop:
        return None

    # If both are present, prioritize the To WaitTime
    if to_wait is not None:
        return to_wait

    if from_wait is not None:
        return from_wait

    # Otherwise, return None
    return None


def determine_wait_time(
    current_link: TXCJourneyPatternTimingLink,
    is_first_stop: bool,
    is_last_stop: bool,
    previous_link: TXCJourneyPatternTimingLink | None = None,
) -> str | None:
    """
    Resolve the current From stop's wait using adjacent journey pattern links.

    Returns:
        The WaitTime to use (string format like 'PT20M') or None if no wait time should be applied
    """
    from_wait = current_link.From.WaitTime if current_link.From else None
    to_wait = previous_link.To.WaitTime if previous_link else None

    return apply_wait_time_rules(from_wait, to_wait, is_first_stop, is_last_stop)


def determine_vehicle_journey_wait_time(
    matching_link: TXCVehicleJourneyTimingLink | None,
    is_first_stop: bool,
    is_last_stop: bool,
    previous_link: TXCVehicleJourneyTimingLink | None = None,
) -> str | None:
    """
    Resolve the current From stop's wait using adjacent vehicle journey links.

    Returns:
        The WaitTime to use (string format like 'PT20M') or None if no wait time should be applied
    """
    from_wait = (
        matching_link.From.WaitTime if matching_link and matching_link.From else None
    )
    to_wait = previous_link.To.WaitTime if previous_link and previous_link.To else None

    return apply_wait_time_rules(from_wait, to_wait, is_first_stop, is_last_stop)


def find_vehicle_journey_timing_links(
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
    link_id: str,
) -> tuple[TXCVehicleJourneyTimingLink | None, timedelta]:
    """
    Find the matching VehicleJourneyTimingLink and possibly the next one.

    Returns:
        tuple: (matching_link, next_link, runtime)
    """
    matching_link: TXCVehicleJourneyTimingLink | None = None
    runtime = timedelta(0)  # Default to 0

    if isinstance(txc_vehicle_journey, TXCVehicleJourney):
        vj_links = txc_vehicle_journey.VehicleJourneyTimingLink
        for _i, vj_link in enumerate(vj_links):
            if vj_link.JourneyPatternTimingLinkRef == link_id:
                matching_link = vj_link
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

    return matching_link, runtime


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
    matching_vj_link, vj_runtime = find_vehicle_journey_timing_links(
        txc_vehicle_journey, link_id
    )

    # Use runtime from VehicleJourneyTimingLink if found
    if matching_vj_link:
        runtime = vj_runtime

    previous_vj_link = None
    if link_context.previous_link:
        previous_vj_link, _ = find_vehicle_journey_timing_links(
            txc_vehicle_journey, link_context.previous_link.id
        )

    # First try to get wait time from VehicleJourneyTimingLink
    wait_time_str = determine_vehicle_journey_wait_time(
        matching_vj_link,
        link_context.is_first_stop,
        link_context.is_last_stop,
        previous_link=previous_vj_link,
    )

    # If no wait time found in VehicleJourneyTimingLink, fall back to JourneyPatternTimingLink
    if wait_time_str is None:
        wait_time_str = determine_wait_time(
            current_link=link_context.current_link,
            is_first_stop=link_context.is_first_stop,
            is_last_stop=link_context.is_last_stop,
            previous_link=link_context.previous_link,
        )

    wait_time = parse_duration(wait_time_str)
    return runtime, wait_time
