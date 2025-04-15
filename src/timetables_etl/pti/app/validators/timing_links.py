"""
Validator functions for JourneyTimingLinks and VehicleJourneyTimingLinks
"""

from dataclasses import dataclass
from decimal import Decimal

from isoduration import DurationParsingException, parse_duration
from isoduration.types import TimeDuration
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..constants import NAMESPACE

log = get_logger()


ZERO_TIME_DURATION = TimeDuration(
    hours=Decimal(0), minutes=Decimal(0), seconds=Decimal(0)
)


@dataclass
class VehicleJourneyRunTimeInfo:
    """
    RuntTime info for a VehicleJourneyTimingLink
    """

    run_time: TimeDuration | None
    has_from: bool
    has_to: bool


def build_vehicle_journey_map(
    root_element: _Element,
) -> dict[str, VehicleJourneyRunTimeInfo]:
    """
    Build a map of { <JourneyPatternTimingLinkRef> : VehicleJourneyRunTimeInfo }
    for all VehicleJourneyTimingLinks
    """
    vehicle_journeys = root_element.xpath("//x:VehicleJourney", namespaces=NAMESPACE)
    vehicle_journey_map: dict[str, VehicleJourneyRunTimeInfo] = {}

    for vehicle_journey in vehicle_journeys:
        timing_links = vehicle_journey.xpath(
            ".//x:VehicleJourneyTimingLink", namespaces=NAMESPACE
        )
        for link in timing_links:
            ref = link.xpath(
                "string(x:JourneyPatternTimingLinkRef)", namespaces=NAMESPACE
            )
            run_time = link.xpath("string(x:RunTime)", namespaces=NAMESPACE)
            has_from = bool(link.xpath("x:From", namespaces=NAMESPACE))
            has_to = bool(link.xpath("x:To", namespaces=NAMESPACE))

            vehicle_journey_map[ref] = VehicleJourneyRunTimeInfo(
                run_time=parse_duration(run_time).time if run_time else None,
                has_from=has_from,
                has_to=has_to,
            )

    return vehicle_journey_map


def validate_journey_pattern_timing_links(
    root_element: _Element,
    vehicle_journey_map: dict[str, VehicleJourneyRunTimeInfo],
) -> list[_Element]:
    """
    Validate JourneyPatternTimingLinks against the associated VehicleJourneyTimingLink data.

    If a JourneyPatternTimingLink has non-zero RunTime,
    any related VehicleJourneyTimingLink should not have To/From elements
    """
    non_compliant_elements: list[_Element] = []
    journey_pattern_sections = root_element.xpath(
        "//x:JourneyPatternSection", namespaces=NAMESPACE
    )
    for section in journey_pattern_sections:
        timing_links = section.xpath(
            ".//x:JourneyPatternTimingLink", namespaces=NAMESPACE
        )
        for link in timing_links:
            link_id = link.get("id")
            run_time = link.xpath("string(x:RunTime)", namespaces=NAMESPACE)

            if not run_time:
                continue

            try:
                time_duration = parse_duration(run_time).time
            except DurationParsingException:
                time_duration = None

            if time_duration and time_duration != ZERO_TIME_DURATION:
                vj_link = vehicle_journey_map.get(link_id)
                if vj_link and (vj_link.has_from or vj_link.has_to):
                    non_compliant_elements.append(link)
    return non_compliant_elements


def validate_run_time(_: _Element | None, elements: list[_Element]) -> list[_Element]:
    """
    Validate run times between JourneyPatternTimingLinks and VehicleJourneyTimingLinks.
    """
    log.info(
        "Validation Start: Timing Link Stops",
    )
    root_element = elements[0]
    vehicle_journey_map = build_vehicle_journey_map(root_element)
    return validate_journey_pattern_timing_links(root_element, vehicle_journey_map)


def validate_timing_link_stops(_: _Element | None, sections: list[_Element]) -> bool:
    """
    Validates that all links in a section are ordered coherently by
    stop point ref.
    """
    log.info(
        "Validation Start: Timing Link Stops",
        sections=len(sections),
    )
    section = sections[0]
    links = section.xpath("x:JourneyPatternTimingLink", namespaces=NAMESPACE)

    prev_link = links[0]
    for curr_link in links[1:]:
        to_ = prev_link.xpath("string(x:To/x:StopPointRef)", namespaces=NAMESPACE)
        from_ = curr_link.xpath("string(x:From/x:StopPointRef)", namespaces=NAMESPACE)

        if from_ != to_:
            return False

        prev_link = curr_link

    return True
