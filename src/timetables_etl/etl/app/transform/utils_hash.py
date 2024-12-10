"""
Hash Functions used by the ETL Pipeline
"""

from structlog.stdlib import get_logger

from ..txc.models import TXCJourneyPattern, TXCJourneyPatternSection

log = get_logger()


def create_hash(values: list[str]) -> str:
    """
    Create a hash value based on the given sequence of values.
    """
    log.info("The hashes", types=type(values[0]))

    print(values)
    return str(hash(tuple(values)))


def create_route_section_hashes(
    journey_pattern_sections: list[TXCJourneyPatternSection],
) -> dict[str, str]:
    """
    In the original BODs, the route_section_hash column is created in the jp_sections
    jp_sections["route_section_hash"]
    Based on the timing_links
    """
    route_section_hashes = {}
    for section in journey_pattern_sections:
        route_link_refs = [
            link.RouteLinkRef for link in section.JourneyPatternTimingLink
        ]
        route_section_hash = create_hash(route_link_refs)
        route_section_hashes[section.id] = route_section_hash
    return route_section_hashes


def create_route_hashes(
    journey_patterns: list[TXCJourneyPattern],
    journey_pattern_sections: list[TXCJourneyPatternSection],
) -> dict[str, str]:
    """
    Create route Hashes that was on journey_patterns["route_hash"]
    """
    route_section_hashes = create_route_section_hashes(journey_pattern_sections)

    routes: dict[str, str] = {}
    for pattern in journey_patterns:
        section_hashes = [
            route_section_hashes[ref] for ref in pattern.JourneyPatternSectionRefs
        ]
        route_hash = create_hash(section_hashes)
        routes[pattern.id] = route_hash

    return routes
