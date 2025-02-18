"""
Stop Calculation Utilities
"""

from typing import Sequence

from common_layer.database.models import NaptanStopPoint
from common_layer.xml.txc.helpers.jps import (
    get_jps_by_id,
    get_stops_from_journey_pattern_section,
)
from common_layer.xml.txc.models import TXCJourneyPattern, TXCJourneyPatternSection
from etl.app.helpers.stop_points import NonExistentNaptanStop
from etl.app.helpers.types import LookupStopPoint
from structlog.stdlib import get_logger

from ..helpers import StopsLookup

log = get_logger()


def get_pattern_stops(
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    atco_location_mapping: StopsLookup,
) -> Sequence[NaptanStopPoint]:
    """
    Get all NaptanStopPoint DB Models for a journey pattern's stop sequence
    """
    stops: list[NaptanStopPoint] = []

    for jps_id in jp.JourneyPatternSectionRefs:
        jps = get_jps_by_id(jps_id, journey_pattern_sections)
        stop_refs = get_stops_from_journey_pattern_section(jps)
        for stop_ref in stop_refs:
            stop_data = atco_location_mapping[stop_ref]
            if isinstance(stop_data, NonExistentNaptanStop):
                log.warning(
                    "Skipping NonExistentNaptanStop", stop_ref=stop_data.atco_code
                )
            else:
                stops.append(stop_data)

    return stops


def get_terminal_stop_points(
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    stop_mapping: StopsLookup,
) -> tuple[LookupStopPoint, LookupStopPoint]:
    """Get first and last NaptanStopPoints in a journey pattern"""
    first_jps = get_jps_by_id(jp.JourneyPatternSectionRefs[0], journey_pattern_sections)
    last_jps = get_jps_by_id(jp.JourneyPatternSectionRefs[-1], journey_pattern_sections)

    first_stop_ref = first_jps.JourneyPatternTimingLink[0].From.StopPointRef
    last_stop_ref = last_jps.JourneyPatternTimingLink[-1].To.StopPointRef

    return (stop_mapping[first_stop_ref], stop_mapping[last_stop_ref])


def get_first_last_stops(
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    stop_mapping: StopsLookup,
) -> tuple[str, str]:
    """Get common names of first and last stops in a journey pattern"""
    first_stop, last_stop = get_terminal_stop_points(
        jp, journey_pattern_sections, stop_mapping
    )
    return (first_stop.common_name, last_stop.common_name)
