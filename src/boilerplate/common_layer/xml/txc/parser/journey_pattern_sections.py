"""
Parse Journey Patterns XML
"""

from random import random
from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import find_section, get_element_bool, get_element_int, get_element_text
from ..models import (
    ActivityT,
    TimingStatusT,
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
)

log = get_logger()


def parse_journey_pattern_stop_usage(
    stop_usage_xml: _Element,
) -> TXCJourneyPatternStopUsage | None:
    """
    From or To section from JourneyPatternSections->JourneyPatternSection->JourneyPatternTimingLink
    """
    stop_usage_id = stop_usage_xml.get("id")
    if not stop_usage_id:

        stop_usage_id = f"JPTL{round(random())}"

    wait_time = get_element_text(stop_usage_xml, "WaitTime")

    activity: ActivityT = (
        cast(ActivityT, text)
        if (text := get_element_text(stop_usage_xml, "Activity")) in get_args(ActivityT)
        else "pickUpAndSetDown"
    )
    dynamic_destination_display = get_element_text(
        stop_usage_xml, "DynamicDestinationDisplay"
    )
    notes = get_element_text(stop_usage_xml, "Notes")
    stop_point_ref = get_element_text(stop_usage_xml, "StopPointRef")

    timing_status: TimingStatusT = (
        cast(TimingStatusT, text)
        if (text := get_element_text(stop_usage_xml, "TimingStatus"))
        in get_args(TimingStatusT)
        else "principalTimingPoint"
    )
    fare_stage_number = get_element_int(stop_usage_xml, "FareStageNumber")
    fare_stage = get_element_bool(stop_usage_xml, "FareStage")

    if not activity or not stop_point_ref or not timing_status:
        log.warning(
            "JourneyPatternStopUsage missing required fields. Skipping.",
            id=stop_usage_id,
            Activity=activity,
            StopPointRef=stop_point_ref,
            TimingStatus=timing_status,
        )
        return None

    return TXCJourneyPatternStopUsage(
        id=stop_usage_id,
        WaitTime=wait_time,
        Activity=activity,
        DynamicDestinationDisplay=dynamic_destination_display,
        Notes=notes,
        StopPointRef=stop_point_ref,
        TimingStatus=timing_status,
        FareStageNumber=fare_stage_number,
        FareStage=fare_stage,
    )


def parse_journey_pattern_timing_link(
    timing_link_xml: _Element,
) -> TXCJourneyPatternTimingLink | None:
    """
    JourneyPatternSections->JourneyPatternSection->JourneyPatternTimingLink
    """
    timing_link_id = timing_link_xml.get("id")
    if not timing_link_id:
        log.warning("JourneyPatternTimingLink missing required id attribute. Skipping.")
        return None

    from_xml = timing_link_xml.find("From")
    if from_xml is None:
        log.warning(
            f"JourneyPatternTimingLink {timing_link_id} missing required From element. Skipping."
        )
        return None

    to_xml = timing_link_xml.find("To")
    if to_xml is None:
        log.warning(
            f"JourneyPatternTimingLink {timing_link_id} missing required To element. Skipping."
        )
        return None

    from_stop_usage = parse_journey_pattern_stop_usage(from_xml)
    to_stop_usage = parse_journey_pattern_stop_usage(to_xml)

    if not from_stop_usage or not to_stop_usage:
        return None

    route_link_ref = get_element_text(timing_link_xml, "RouteLinkRef")
    run_time = get_element_text(timing_link_xml, "RunTime")
    distance = get_element_text(timing_link_xml, "Distance")

    if not route_link_ref or not run_time:
        log.warning(
            "JourneyPatternTimingLink missing required fields. Skipping.",
            id=timing_link_id,
            RouteLinkRef=route_link_ref,
            RunTime=run_time,
        )
        return None

    return TXCJourneyPatternTimingLink(
        id=timing_link_id,
        From=from_stop_usage,
        To=to_stop_usage,
        RouteLinkRef=route_link_ref,
        RunTime=run_time,
        Distance=distance,
    )


def parse_journey_pattern_section(
    section_xml: _Element,
) -> TXCJourneyPatternSection | None:
    """
    JourneyPatternSections->JourneyPatternSection
    """
    section_id = section_xml.get("id")

    if not section_id:
        log.warning("JourneyPatternSection missing required id attribute. Skipping.")
        return None

    timing_links: list[TXCJourneyPatternTimingLink] = []
    for timing_link_xml in section_xml.findall("JourneyPatternTimingLink"):
        timing_link = parse_journey_pattern_timing_link(timing_link_xml)
        if timing_link:
            timing_links.append(timing_link)

    if not timing_links:
        log.warning(
            f"JourneyPatternSection {section_id} has no valid JourneyPatternTimingLinks. Skipping."
        )
        return None

    return TXCJourneyPatternSection(
        id=section_id,
        JourneyPatternTimingLink=timing_links,
    )


def parse_journey_pattern_sections(
    xml_data: _Element,
) -> list[TXCJourneyPatternSection]:
    """
    Parse XML for list of JourneyPatternSections
    """
    try:
        section = find_section(xml_data, "JourneyPatternSections")
    except ValueError:
        log.warning("JourneyPatternSections Not Found")
        return []

    journey_pattern_sections: list[TXCJourneyPatternSection] = []
    for section_xml in section.findall("JourneyPatternSection"):
        journey_pattern_section = parse_journey_pattern_section(section_xml)
        if journey_pattern_section:
            journey_pattern_sections.append(journey_pattern_section)
    log.info("Parsed TXC Journey Pattern Sections", count=len(journey_pattern_sections))
    return journey_pattern_sections
