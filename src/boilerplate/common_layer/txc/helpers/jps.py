"""
Journey Pattern Section Helpers
"""

from ..models import TXCJourneyPatternSection


def get_jps_by_id(
    jps_id: str,
    journey_pattern_section_list: list[TXCJourneyPatternSection],
) -> TXCJourneyPatternSection:
    """
    Get the TXC JourneyPatternSection out of a list by ID
    """
    return next(jps for jps in journey_pattern_section_list if jps.id == jps_id)


def get_stops_from_journey_pattern_section(
    section: TXCJourneyPatternSection,
) -> list[str]:
    """
    Generate a list of stop point references from a single journey pattern section.
    Takes the From of each link, and then adds the To of the final stop at the end
    So that stops aren't duplicated
    """
    stops: list[str] = []
    for link in section.JourneyPatternTimingLink:
        stops.append(link.From.StopPointRef)
    stops.append(section.JourneyPatternTimingLink[-1].To.StopPointRef)
    return stops


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
