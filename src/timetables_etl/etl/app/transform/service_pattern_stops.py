"""
Processing for transmodel_servicepatternstop
"""

import re
from datetime import datetime, time, timedelta
from typing import Sequence

from structlog.stdlib import get_logger

from ..database.models.model_naptan import NaptanStopPoint
from ..database.models.model_transmodel import (
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelStopActivity,
    TransmodelVehicleJourney,
)
from ..txc.models import TXCVehicleJourney
from ..txc.models.txc_journey_pattern import (
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
)

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


def parse_time(time_value: str | time | None) -> time | None:
    """Parse string time value to time object"""
    if time_value is None:
        return None
    if isinstance(time_value, time):
        return time_value
    try:
        return datetime.strptime(time_value, "%H:%M:%S").time()
    except ValueError:
        log.error("Invalid time format", time_value=time_value)
        return None


def calculate_next_time(
    current: str | time | None, runtime: timedelta, wait: timedelta
) -> time | None:
    """Calculate next departure time including wait time, handling optional times"""
    parsed_time = parse_time(current)
    if parsed_time is None:
        return None

    base = datetime.combine(datetime.today(), parsed_time)
    next_time = base + runtime + wait
    return next_time.time()


def create_stop(
    stop_usage: TXCJourneyPatternStopUsage,
    naptan_stop: NaptanStopPoint,
    service_pattern: TransmodelServicePattern,
    vehicle_journey: TransmodelVehicleJourney,
    departure_time: time | None,
    auto_sequence: int,
    activity_map: dict[str, TransmodelStopActivity],
) -> TransmodelServicePatternStop | None:
    """
    Create a TransmodelServicePatternStop for a single stop in the vehicle journey
    """
    activity = activity_map.get(stop_usage.Activity)
    if not activity:
        log.error(
            "Stop activity not found - skipping stop",
            requested_activity=stop_usage.Activity,
            available_activities=list(activity_map.keys()),
            stop_point=stop_usage.StopPointRef,
            vehicle_journey_id=vehicle_journey.id,
        )
        return None

    return TransmodelServicePatternStop(
        sequence_number=int(stop_usage.SequenceNumber or auto_sequence),
        atco_code=stop_usage.StopPointRef,
        naptan_stop_id=naptan_stop.id if naptan_stop else None,
        service_pattern_id=service_pattern.id,
        departure_time=departure_time,
        is_timing_point=stop_usage.TimingStatus == "principalTimingPoint",
        txc_common_name=naptan_stop.common_name,
        vehicle_journey_id=vehicle_journey.id,
        stop_activity_id=activity.id,
        auto_sequence_number=auto_sequence,
    )


def get_pattern_timing(
    txc_vehicle_journey: TXCVehicleJourney,
    link_id: str,
    base_link_runtime: str,
) -> tuple[timedelta, timedelta]:
    """
    Get runtime and wait time, handling both vehicle journey types
    VehicleJourneyTimingLink override the JourneyPatternSectionTimingLinks
    """
    has_timing_links = len(txc_vehicle_journey.VehicleJourneyTimingLink) > 0

    if has_timing_links:
        vj_link = next(
            (
                vl
                for vl in txc_vehicle_journey.VehicleJourneyTimingLink
                if vl.JourneyPatternTimingLinkRef == link_id
            ),
            None,
        )
        if vj_link:
            wait_time = parse_duration(vj_link.From.WaitTime if vj_link.From else None)
            run_time = parse_duration(vj_link.RunTime)
            return run_time, wait_time

        available_links = [
            vl.JourneyPatternTimingLinkRef
            for vl in txc_vehicle_journey.VehicleJourneyTimingLink
        ]
        log.warning(
            "Missing timing link in vehicle journey - using base runtime",
            vehicle_journey_id=txc_vehicle_journey.VehicleJourneyCode,
            requested_link=link_id,
            available_links=available_links,
        )

    return parse_duration(base_link_runtime), timedelta(0)


def generate_pattern_stops(
    tm_service_pattern: TransmodelServicePattern,
    tm_vehicle_journey: TransmodelVehicleJourney,
    txc_vehicle_journey: TXCVehicleJourney,
    jp_sections: list[TXCJourneyPatternSection],
    stop_sequence: Sequence[NaptanStopPoint],
    activity_map: dict[str, TransmodelStopActivity],
) -> list[TransmodelServicePatternStop]:
    """
    Generate data for transmodel_servicepatternstop
    Each TXCVehicleJourney has a set of stops that need their own rows in the DB
    """
    log.info(
        "Starting pattern stops generation",
        jp_section_count=len(jp_sections),
        stop_count=len(stop_sequence),
        activity_count=len(activity_map),
        vehicle_journey=txc_vehicle_journey.VehicleJourneyCode,
    )
    pattern_stops: list[TransmodelServicePatternStop] = []
    current_time: time | None = tm_vehicle_journey.start_time
    auto_sequence: int = 0

    stop_iter = iter(stop_sequence)
    naptan_stop = next(stop_iter)

    for section in jp_sections:
        for link in section.JourneyPatternTimingLink:
            # Handle 'From' stop
            stop = create_stop(
                stop_usage=link.From,
                naptan_stop=naptan_stop,
                service_pattern=tm_service_pattern,
                vehicle_journey=tm_vehicle_journey,
                departure_time=current_time,
                auto_sequence=auto_sequence,
                activity_map=activity_map,
            )
            if stop:
                pattern_stops.append(stop)
                auto_sequence += 1

            runtime, wait_time = get_pattern_timing(
                txc_vehicle_journey,
                link.id,
                link.RunTime,
            )
            current_time = calculate_next_time(current_time, runtime, wait_time)

            try:
                naptan_stop = next(stop_iter)
            except StopIteration:
                log.error(
                    "Ran out of stops before finishing pattern",
                    section_id=section.id,
                    link_id=link.id,
                    pattern_id=tm_service_pattern.id,
                )
                return pattern_stops

            # Handle 'To' stop if it's the last link
            if link == section.JourneyPatternTimingLink[-1]:
                stop = create_stop(
                    stop_usage=link.To,
                    naptan_stop=naptan_stop,
                    service_pattern=tm_service_pattern,
                    vehicle_journey=tm_vehicle_journey,
                    departure_time=current_time,
                    auto_sequence=auto_sequence,
                    activity_map=activity_map,
                )
                if stop:
                    pattern_stops.append(stop)
                    auto_sequence += 1
    log.info(
        "Generated Service Pattern Stops",
        txc_vj=txc_vehicle_journey.VehicleJourneyCode,
        tm_vj=tm_vehicle_journey.id,
        tm_service_pattern=tm_service_pattern.id,
        stop_count=len(pattern_stops),
    )
    return pattern_stops
