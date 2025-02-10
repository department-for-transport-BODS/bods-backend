"""
Stops Helpers
"""

from common_layer.xml.txc.helpers.jps import (
    get_jps_by_id,
    get_stops_from_journey_pattern_section,
)
from common_layer.xml.txc.models import TXCJourneyPatternSection


def get_stops_from_sections(
    section_refs: list[str], journey_pattern_sections: list[TXCJourneyPatternSection]
) -> list[str]:
    """
    Get the list of stops from a list of JourneyPatternSectionRefs
    """
    stops: list[str] = []
    for jps_id in section_refs:
        jps = get_jps_by_id(jps_id, journey_pattern_sections)
        section_stops = get_stops_from_journey_pattern_section(jps)
        if not stops:
            stops.extend(section_stops)
        else:
            stops.extend(section_stops[1:])
    return stops
