"""
Stop Calculation Utilities
"""

from typing import Sequence

from ..database.models import NaptanStopPoint
from ..txc.helpers.jps import get_jps_by_id, get_stops_from_journey_pattern_section
from ..txc.models.txc_journey_pattern import TXCJourneyPatternSection
from ..txc.models.txc_service import TXCJourneyPattern


def get_pattern_stops(
    jp: TXCJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    atco_location_mapping: dict[str, NaptanStopPoint],
) -> Sequence[NaptanStopPoint]:
    """
    Get all NaptanStopPoint DB Models for a journey pattern's stop sequence
    """
    stops: list[NaptanStopPoint] = []

    for jps_id in jp.JourneyPatternSectionRefs:
        jps = get_jps_by_id(jps_id, journey_pattern_sections)
        stop_refs = get_stops_from_journey_pattern_section(jps)
        stops.extend(atco_location_mapping[stop_ref] for stop_ref in stop_refs)

    return stops
