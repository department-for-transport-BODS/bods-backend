"""
Processing for transmodel_servicepatternstop
"""

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Iterator, Sequence

from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelStopActivity,
    TransmodelVehicleJourney,
)
from common_layer.xml.txc.models import (
    TXCFlexibleVehicleJourney,
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCVehicleJourney,
)
from structlog.stdlib import get_logger

from ..helpers.types import LookupStopPoint, StopsLookup

log = get_logger()


@dataclass
class StopContext:
    """Context for creating a service pattern stop"""

    auto_sequence: int
    service_pattern: TransmodelServicePattern
    vehicle_journey: TransmodelVehicleJourney
    departure_time: time | None


@dataclass
class StopData:
    """Data for a service pattern stop"""

    stop_usage: TXCJourneyPatternStopUsage
    naptan_stop: LookupStopPoint


@dataclass
class GeneratePatternStopsContext:
    """Context for generating pattern stops"""

    jp_sections: list[TXCJourneyPatternSection]
    stop_sequence: Sequence[NaptanStopPoint]
    activity_map: dict[str, TransmodelStopActivity]
    naptan_stops_lookup: StopsLookup


@dataclass
class JourneySectionContext:
    """Context for journey section processing"""

    service_pattern: TransmodelServicePattern
    vehicle_journey: TransmodelVehicleJourney
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney
    pattern_context: GeneratePatternStopsContext
    naptan_stops_lookup: StopsLookup


@dataclass
class SectionProcessingState:
    """State for processing journey pattern sections"""

    current_time: time | None
    auto_sequence: int
    pattern_stops: list[TransmodelServicePatternStop]


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
    stop_data: StopData,
    context: StopContext,
    activity_map: dict[str, TransmodelStopActivity],
) -> TransmodelServicePatternStop | None:
    """
    Create a TransmodelServicePatternStop for a single stop in the vehicle journey
    """
    activity = activity_map.get(stop_data.stop_usage.Activity)
    if not activity:
        log.error(
            "Stop activity not found - skipping stop",
            requested_activity=stop_data.stop_usage.Activity,
            available_activities=list(activity_map.keys()),
            stop_point=stop_data.stop_usage.StopPointRef,
            vehicle_journey_id=context.vehicle_journey.id,
        )
        return None

    naptan_stop_id = (
        stop_data.naptan_stop.id
        if isinstance(stop_data.naptan_stop, NaptanStopPoint)
        else None
    )
    return TransmodelServicePatternStop(
        sequence_number=int(
            stop_data.stop_usage.SequenceNumber or context.auto_sequence
        ),
        atco_code=stop_data.stop_usage.StopPointRef,
        naptan_stop_id=naptan_stop_id,
        service_pattern_id=context.service_pattern.id,
        departure_time=context.departure_time,
        is_timing_point=stop_data.stop_usage.TimingStatus == "principalTimingPoint",
        txc_common_name=stop_data.naptan_stop.common_name,
        vehicle_journey_id=context.vehicle_journey.id,
        stop_activity_id=activity.id,
        auto_sequence_number=context.auto_sequence,
    )


def get_pattern_timing(
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
    link_id: str,
    base_link_runtime: str,
) -> tuple[timedelta, timedelta]:
    """
    Get runtime and wait time, handling both vehicle journey types
    VehicleJourneyTimingLink override the JourneyPatternSectionTimingLinks
    """
    default_timing = (parse_duration(base_link_runtime), timedelta(0))

    match txc_vehicle_journey:
        case TXCFlexibleVehicleJourney():
            return default_timing

        case TXCVehicleJourney() if not txc_vehicle_journey.VehicleJourneyTimingLink:
            return default_timing

        case TXCVehicleJourney():
            if vj_link := next(
                (
                    vl
                    for vl in txc_vehicle_journey.VehicleJourneyTimingLink
                    if vl.JourneyPatternTimingLinkRef == link_id
                ),
                None,
            ):
                return (
                    parse_duration(vj_link.RunTime),
                    parse_duration(vj_link.From.WaitTime if vj_link.From else None),
                )

            # Link not found, log warning
            log.warning(
                "Missing timing link in vehicle journey - using base runtime",
                vehicle_journey_id=txc_vehicle_journey.VehicleJourneyCode,
                requested_link=link_id,
                available_links=[
                    vl.JourneyPatternTimingLinkRef
                    for vl in txc_vehicle_journey.VehicleJourneyTimingLink
                ],
            )
            return default_timing

        case _:
            raise ValueError(
                f"Unknown vehicle journey type: {type(txc_vehicle_journey)}"
            )


def is_duplicate_stop(
    current_stop_ref: str,
    current_sequence: int,
    previous_stop: TransmodelServicePatternStop | None,
) -> bool:
    """
    Determine if a stop would be a duplicate at a section boundary.
    This happens when:
        - There are multiple JourneyPatternSectionRefs for a Journey Pattern
    Meaning that the last stop of the JPS is the first stop of the next JPS
    """
    if not previous_stop or previous_stop.auto_sequence_number is None:
        return False

    return (
        previous_stop.atco_code == current_stop_ref
        and current_sequence == previous_stop.auto_sequence_number + 1
    )


def create_pattern_stop(
    stop_data: StopData,
    stop_context: StopContext,
    activity_map: dict[str, TransmodelStopActivity],
) -> TransmodelServicePatternStop | None:
    """
    Create a new service pattern stop if appropriate.
    """
    if stop := create_stop(stop_data, stop_context, activity_map):
        return stop
    return None


def process_journey_pattern_section(
    section: TXCJourneyPatternSection,
    state: SectionProcessingState,
    context: JourneySectionContext,
) -> tuple[bool, SectionProcessingState]:
    """Process a single journey pattern section"""
    log.info(f"Processing section {section.id}")
    for link in section.JourneyPatternTimingLink:
        log.info(
            f"Handling link From {link.From.StopPointRef} to {link.To.StopPointRef}"
        )
        # Handle 'From' stop
        if not is_duplicate_stop(
            current_stop_ref=link.From.StopPointRef,
            current_sequence=state.auto_sequence,
            previous_stop=state.pattern_stops[-1] if state.pattern_stops else None,
        ):
            stop_context = StopContext(
                service_pattern=context.service_pattern,
                vehicle_journey=context.vehicle_journey,
                auto_sequence=state.auto_sequence,
                departure_time=state.current_time,
            )

            naptan_stop = context.naptan_stops_lookup[link.From.StopPointRef]
            stop_data = StopData(
                stop_usage=link.From,
                naptan_stop=naptan_stop,
            )

            if stop := create_pattern_stop(
                stop_data, stop_context, context.pattern_context.activity_map
            ):
                state.pattern_stops.append(stop)
                state.auto_sequence += 1
        else:
            log.debug(
                "Skipping duplicate stop at section boundary",
                atco_code=link.From.StopPointRef,
                sequence=state.auto_sequence,
            )

        # Handle timing updates
        runtime, wait_time = get_pattern_timing(
            context.txc_vehicle_journey,
            link.id,
            link.RunTime,
        )
        state.current_time = calculate_next_time(state.current_time, runtime, wait_time)

        # Handle 'To' stop if it's the last link
        if link == section.JourneyPatternTimingLink[-1]:
            stop_context = StopContext(
                service_pattern=context.service_pattern,
                vehicle_journey=context.vehicle_journey,
                auto_sequence=state.auto_sequence,
                departure_time=state.current_time,
            )
            naptan_stop = context.naptan_stops_lookup[link.To.StopPointRef]
            stop_data = StopData(
                stop_usage=link.To,
                naptan_stop=naptan_stop,
            )

            if stop := create_pattern_stop(
                stop_data, stop_context, context.pattern_context.activity_map
            ):
                state.pattern_stops.append(stop)
                state.auto_sequence += 1

    return True, state


def generate_pattern_stops(
    service_pattern: TransmodelServicePattern,
    vehicle_journey: TransmodelVehicleJourney,
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
    context: GeneratePatternStopsContext,
) -> list[TransmodelServicePatternStop]:
    """
    Generate data for transmodel_servicepatternstop
    Each TXCVehicleJourney has a set of stops that need their own rows in the DB
    """
    log.info(
        "Starting pattern stops generation",
        jp_section_count=len(context.jp_sections),
        stop_count=len(context.stop_sequence),
        activity_count=len(context.activity_map),
        vehicle_journey=txc_vehicle_journey.VehicleJourneyCode,
    )

    state = SectionProcessingState(
        current_time=vehicle_journey.start_time,
        auto_sequence=0,
        pattern_stops=[],
    )

    journey_context = JourneySectionContext(
        service_pattern=service_pattern,
        vehicle_journey=vehicle_journey,
        txc_vehicle_journey=txc_vehicle_journey,
        pattern_context=context,
        naptan_stops_lookup=context.naptan_stops_lookup,
    )

    for section in context.jp_sections:
        success, state = process_journey_pattern_section(
            section=section,
            state=state,
            context=journey_context,
        )
        if not success:
            break

    log.info(
        "Generated Service Pattern Stops",
        txc_vj=txc_vehicle_journey.VehicleJourneyCode,
        tm_vj=vehicle_journey.id,
        tm_service_pattern=service_pattern.id,
        stop_count=len(state.pattern_stops),
    )

    return state.pattern_stops
