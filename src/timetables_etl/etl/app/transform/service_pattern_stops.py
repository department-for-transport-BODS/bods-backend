"""
Processing for transmodel_servicepatternstop
"""

from datetime import datetime, time, timedelta

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
    TXCVehicleJourney,
)
from structlog.stdlib import get_logger

from .models_context import (
    GeneratePatternStopsContext,
    JourneySectionContext,
    LinkContext,
    SectionProcessingState,
    StopContext,
    StopData,
)
from .service_pattern_stops_durations import get_pattern_timing

log = get_logger()


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
    stop_activity_id_map: dict[str, int],
) -> TransmodelServicePatternStop | None:
    """
    Create a TransmodelServicePatternStop for a single stop in the vehicle journey
    """
    activity_id = stop_activity_id_map.get(stop_data.stop_usage.Activity)
    if not activity_id:
        log.error(
            "Stop activity not found - skipping stop",
            requested_activity=stop_data.stop_usage.Activity,
            available_activities=list(stop_activity_id_map.keys()),
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
        stop_activity_id=activity_id,
        auto_sequence_number=context.auto_sequence,
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
    stop_activity_id_map: dict[str, int],
) -> TransmodelServicePatternStop | None:
    """
    Create a new service pattern stop if appropriate.
    """
    if stop := create_stop(stop_data, stop_context, stop_activity_id_map):
        return stop
    return None


def process_journey_pattern_section(
    section: TXCJourneyPatternSection,
    state: SectionProcessingState,
    context: JourneySectionContext,
) -> tuple[bool, SectionProcessingState]:
    """
    Process a single journey pattern section with enhanced wait time handling

    This implementation uses the custom wait time selection logic:
    1. Add WaitTime either from the From or the To depending on where it is present
    2. If both From and To are present, pick the <To> WaitTime
    3. The first stop will always take the <From> WaitTime
    4. The last stop will not take the <To> WaitTime
    5. If a waittime is <WaitTime>PT0S</WaitTime> we consider that not present
    """
    log.info("Processing section", section_id=section.id)

    # Get all links in the section for easier access to next links
    links = section.JourneyPatternTimingLink
    total_links = len(links)

    for i, link in enumerate(links):
        # Determine if this is the first stop in the overall journey
        is_first_stop = state.auto_sequence == 0
        next_link = links[i + 1] if i < total_links - 1 else None

        # Handle timing updates with our enhanced wait time logic
        link_context = LinkContext(
            current_link=link,
            next_link=next_link,
            is_first_stop=is_first_stop,
            is_last_stop=False,  # This is not the last stop since we're processing a From
        )

        runtime, wait_time = get_pattern_timing(
            txc_vehicle_journey=context.txc_vehicle_journey,
            link_id=link.id,
            link_context=link_context,
            base_link_runtime=link.RunTime,
        )
        # Always add wait time before a stop is added
        state.current_time = calculate_next_time(
            state.current_time,
            timedelta(
                days=0,
                seconds=0,
                microseconds=0,
                milliseconds=0,
                minutes=0,
                hours=0,
                weeks=0,
            ),
            wait_time,
        )

        # Handle 'From' stop
        if not is_duplicate_stop(
            current_stop_ref=link.From.StopPointRef,
            current_sequence=state.auto_sequence,
            previous_stop=state.pattern_stops[-1] if state.pattern_stops else None,
        ):
            if stop := create_pattern_stop(
                StopData(
                    stop_usage=link.From,
                    naptan_stop=context.naptan_stops_lookup[link.From.StopPointRef],
                ),
                StopContext(
                    service_pattern=context.service_pattern,
                    vehicle_journey=context.vehicle_journey,
                    auto_sequence=state.auto_sequence,
                    departure_time=state.current_time,
                ),
                context.pattern_context.stop_activity_id_map,
            ):
                state.pattern_stops.append(stop)
                state.auto_sequence += 1
        else:
            log.debug(
                "Skipping duplicate stop at section boundary",
                atco_code=link.From.StopPointRef,
                sequence=state.auto_sequence,
            )

        # Add runtime after a stop is added to calculate the correct current_time for next stop
        state.current_time = calculate_next_time(
            state.current_time,
            runtime,
            timedelta(
                days=0,
                seconds=0,
                microseconds=0,
                milliseconds=0,
                minutes=0,
                hours=0,
                weeks=0,
            ),
        )

        # Handle 'To' stop if it's the last link in the section
        if i == total_links - 1:
            if stop := create_pattern_stop(
                StopData(
                    stop_usage=link.To,
                    naptan_stop=context.naptan_stops_lookup[link.To.StopPointRef],
                ),
                StopContext(
                    service_pattern=context.service_pattern,
                    vehicle_journey=context.vehicle_journey,
                    auto_sequence=state.auto_sequence,
                    departure_time=state.current_time,
                ),
                context.pattern_context.stop_activity_id_map,
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
        activity_count=len(context.stop_activity_id_map),
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
