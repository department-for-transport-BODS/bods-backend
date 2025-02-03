"""
Helper Functions to Query the TXCService Pydantic Models
"""

from datetime import date

from structlog.stdlib import get_logger

from ..models import (
    ActivityT,
    TransportModeT,
    TXCFixedStopUsage,
    TXCFlexibleJourneyPattern,
    TXCFlexibleStopUsage,
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCService,
)
from .jps import get_jps_by_id, get_stops_from_journey_pattern_section

log = get_logger()


def get_line_names(service: TXCService) -> list[str]:
    """Get all line names from a single TXC Service"""
    line_names = [line.LineName for line in service.Lines]

    if not line_names:
        log.warning("No line names found for service", service_code=service.ServiceCode)

    return line_names


def get_all_line_names(services: list[TXCService]) -> list[str]:
    """Get all line names across multiple TXC Services"""
    line_names = [name for service in services for name in get_line_names(service)]

    if not line_names:
        log.warning("No line names found across services")

    return line_names


def get_service_start_dates(services: list[TXCService]) -> list[date]:
    """Get all service start dates."""
    if not services:
        log.warning("No services found")
        return []
    return [service.StartDate for service in services]


def get_service_end_dates(services: list[TXCService]) -> list[date]:
    """Get all service end dates."""
    if not services:
        log.warning("No services found")
        return []
    dates = [service.EndDate for service in services if service.EndDate is not None]
    if not dates:
        log.warning("No service end dates found")
    return dates


def get_service_origins(services: list[TXCService]) -> list[str]:
    """Get origins from both standard and flexible services."""
    origins = [
        origin
        for service in services
        if (
            origin := (
                (service.StandardService and service.StandardService.Origin)
                or (service.FlexibleService and service.FlexibleService.Origin)
            )
        )
    ]

    if not origins:
        log.warning("No services with origins found")
    return origins


def get_service_destinations(services: list[TXCService]) -> list[str]:
    """Get destinations from both standard and flexible services."""
    destinations = [
        destination
        for service in services
        if (
            destination := (
                (service.StandardService and service.StandardService.Destination)
                or (service.FlexibleService and service.FlexibleService.Destination)
            )
        )
    ]

    if not destinations:
        log.warning("No services with destinations found")
    return destinations


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


def extract_flexible_pattern_stop_refs(
    flexible_jp: TXCFlexibleJourneyPattern,
) -> list[str]:
    """
    Extract all stop references from a flexible journey pattern.
    Includes both FixedStopUsage and FlexibleStopUsage stops.
    """
    stop_refs: list[str] = []

    stop_refs.extend(
        stop_usage.StopPointRef for stop_usage in flexible_jp.StopPointsInSequence
    )

    stop_refs.extend(
        flexible_zone.StopPointRef for flexible_zone in flexible_jp.FlexibleZones
    )

    return stop_refs


def get_journey_pattern_stops(
    jp: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    journey_pattern_sections: list[TXCJourneyPatternSection] | None = None,
) -> list[str]:
    """
    Get stop point references for both standard and flexible patterns
    """
    match jp:
        case TXCFlexibleJourneyPattern():
            return extract_flexible_pattern_stop_refs(jp)
        case TXCJourneyPattern():
            if not journey_pattern_sections:
                raise ValueError(
                    "journey_pattern_sections required for standard journey patterns"
                )
            return get_stops_from_sections(
                jp.JourneyPatternSectionRefs, journey_pattern_sections
            )
    raise ValueError(f"Unknown journey pattern type: {type(jp)}")


def get_stop_activity_details(
    stop_point: TXCFixedStopUsage | TXCFlexibleStopUsage,
) -> tuple[bool, ActivityT]:
    """
    Get timing point status and activity type for a Flexible Stop

    """
    match stop_point:
        case TXCFixedStopUsage():
            is_timing_point = stop_point.TimingStatus == "principalPoint"
            activity_type: ActivityT = "pickUpAndSetDown"
            return is_timing_point, activity_type
        case TXCFlexibleStopUsage():
            is_timing_point = False
            activity_type = "pickUpAndSetDown"
            return is_timing_point, activity_type

    raise ValueError(f"Unknown stop type: {type(stop_point)}")


def get_service_modes(services: list[TXCService]) -> list[TransportModeT]:
    """
    Get a list of of modes
    """
    modes: list[TransportModeT] = []
    for service in services:
        modes.append(service.Mode)
    return modes
