"""
Parse XML Services Section
"""

from datetime import date
from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import (
    find_section,
    get_elem_bool_default,
    get_element_date,
    get_element_text,
    get_element_texts,
    parse_xml_int,
)
from ..models import (
    TransportModeT,
    TXCFlexibleService,
    TXCJourneyPattern,
    TXCLine,
    TXCLineDescription,
    TXCService,
    TXCStandardService,
)
from .services_flexible import parse_flexible_service

log = get_logger()


def parse_line_description(line_description_xml: _Element) -> TXCLineDescription | None:
    """
    Services -> Service -> Line -> InboundDescription/OutboundDescription
    """
    origin = get_element_text(line_description_xml, "Origin")
    destination = get_element_text(line_description_xml, "Destination")
    description = get_element_text(line_description_xml, "Description")

    vias_xml = line_description_xml.find("Vias")
    vias = get_element_texts(vias_xml, "Via") if vias_xml is not None else []
    if not description:
        log.warning("Service Line Description Missing")
        return None

    return TXCLineDescription(
        Origin=origin, Destination=destination, Description=description, Vias=vias
    )


def parse_line(line_xml: _Element) -> TXCLine | None:
    """
    Services -> Service -> Line
    """
    line_id = line_xml.get("id")
    if not line_id:
        log.warning("Line missing required id attribute. Skipping.")
        return None

    line_name = get_element_text(line_xml, "LineName")
    if not line_name:
        log.warning(f"Line {line_id} missing required LineName. Skipping.")
        return None

    marketing_name = get_element_text(line_xml, "MarketingName")
    outbound_description_xml = line_xml.find("OutboundDescription")
    outbound_description = (
        parse_line_description(outbound_description_xml)
        if outbound_description_xml is not None
        else None
    )
    inbound_description_xml = line_xml.find("InboundDescription")
    inbound_description = (
        parse_line_description(inbound_description_xml)
        if inbound_description_xml is not None
        else None
    )

    return TXCLine(
        id=line_id,
        LineName=line_name,
        MarketingName=marketing_name,
        OutboundDescription=outbound_description,
        InboundDescription=inbound_description,
    )


def parse_journey_pattern(journey_pattern_xml: _Element) -> TXCJourneyPattern | None:
    """
    Services -> Service -> StandardService -> Journey Pattern
    """
    journey_pattern_id = journey_pattern_xml.get("id")
    if not journey_pattern_id:
        log.warning("JourneyPattern missing required id attribute. Skipping.")
        return None

    private_code = get_element_text(journey_pattern_xml, "PrivateCode")
    destination_display = get_element_text(journey_pattern_xml, "DestinationDisplay")
    operator_ref = get_element_text(journey_pattern_xml, "OperatorRef")
    direction = get_element_text(journey_pattern_xml, "Direction")
    route_ref = get_element_text(journey_pattern_xml, "RouteRef")
    journey_pattern_section_refs = get_element_texts(
        journey_pattern_xml, "JourneyPatternSectionRefs"
    )
    description = get_element_text(journey_pattern_xml, "Description")
    layover_point = get_element_text(journey_pattern_xml, "LayoverPoint")

    if (
        not destination_display
        or not direction
        or not route_ref
        or not journey_pattern_section_refs
    ):
        log.warning(
            "JourneyPattern missing required fields. Skipping.",
            id=journey_pattern_id,
            DestinationDisplay=destination_display,
            Direction=direction,
            RouteRef=route_ref,
            JourneyPatternSectionRefs=journey_pattern_section_refs,
        )
        return None

    return TXCJourneyPattern(
        id=journey_pattern_id,
        PrivateCode=private_code,
        DestinationDisplay=destination_display,
        OperatorRef=operator_ref,
        Direction=direction,
        RouteRef=route_ref,
        JourneyPatternSectionRefs=journey_pattern_section_refs,
        Description=description,
        LayoverPoint=layover_point,
    )


def parse_standard_service(standard_service_xml: _Element) -> TXCStandardService | None:
    """
    Services -> Service -> StandardService
    """
    origin = get_element_text(standard_service_xml, "Origin")
    destination = get_element_text(standard_service_xml, "Destination")

    if not origin or not destination:
        log.warning(
            "StandardService missing required Origin or Destination. Skipping.",
            Origin=origin,
            Destination=destination,
        )
        return None

    journey_patterns: list[TXCJourneyPattern] = []
    for journey_pattern_xml in standard_service_xml.findall("JourneyPattern"):
        journey_pattern = parse_journey_pattern(journey_pattern_xml)
        if journey_pattern:
            journey_patterns.append(journey_pattern)

    return TXCStandardService(
        Origin=origin,
        Destination=destination,
        JourneyPattern=journey_patterns,
    )


def parse_operating_period(service_xml: _Element) -> tuple[date | None, date | None]:
    """
    Parse the operating period from OperatingPeriod in a TXC Service
    """
    operating_period_xml = service_xml.find("OperatingPeriod")
    if operating_period_xml is not None:
        start_date = get_element_date(operating_period_xml, "StartDate")
        end_date = get_element_date(operating_period_xml, "EndDate")
        return start_date, end_date
    return None, None


def parse_service_type(
    service_xml: _Element,
) -> tuple[TXCStandardService | None, TXCFlexibleService | None]:
    """Parse standard or flexible service from service XML."""
    standard_service_xml = service_xml.find("StandardService")
    standard_service = (
        parse_standard_service(standard_service_xml)
        if standard_service_xml is not None
        else None
    )

    flexible_service_xml = service_xml.find("FlexibleService")
    flexible_service = (
        parse_flexible_service(flexible_service_xml)
        if flexible_service_xml is not None
        else None
    )

    return standard_service, flexible_service


def parse_transport_mode(service_xml: _Element) -> TransportModeT:
    """Parse transport mode from service XML."""
    text = get_element_text(service_xml, "Mode")
    return cast(TransportModeT, text) if text in get_args(TransportModeT) else "bus"


def parse_lines_list(service_xml: _Element) -> list[TXCLine]:
    """Parse lines from service XML."""
    lines: list[TXCLine] = []
    for line_xml in service_xml.findall("Lines/Line"):
        line = parse_line(line_xml)
        if line:
            lines.append(line)
    return lines


def parse_service(service_xml: _Element) -> TXCService | None:
    """
    Parse a single TXC Service inside a Services block
    """
    start_date, end_date = parse_operating_period(service_xml)
    service_code = get_element_text(service_xml, "ServiceCode")
    registered_operator_ref = get_element_text(service_xml, "RegisteredOperatorRef")
    public_use = get_elem_bool_default(service_xml, "PublicUse", True)

    standard_service, flexible_service = parse_service_type(service_xml)
    mode = parse_transport_mode(service_xml)

    if (
        not isinstance(service_code, str)
        or not isinstance(registered_operator_ref, str)
        or not isinstance(start_date, date)
        or (not standard_service and not flexible_service)
    ):
        log.error(
            "Service missing required fields. Skipping.",
            ServiceCode=service_code,
            RegisteredOperatorRef=registered_operator_ref,
            StandardService=standard_service,
            FlexibleService=flexible_service,
            StartDate=start_date,
        )
        return None

    lines = parse_lines_list(service_xml)

    return TXCService(
        RevisionNumber=parse_xml_int(service_xml, "RevisionNumber") or 0,
        ServiceCode=service_code,
        PrivateCode=get_element_text(service_xml, "PrivateCode"),
        RegisteredOperatorRef=registered_operator_ref,
        PublicUse=public_use,
        StartDate=start_date,
        EndDate=end_date,
        StandardService=standard_service,
        FlexibleService=flexible_service,
        Lines=lines,
        Mode=mode,
    )


def parse_services(xml_data: _Element) -> list[TXCService]:
    """
    Parse Services Section of TXC XML
    """
    try:
        section = find_section(xml_data, "Services")
    except ValueError:
        return []

    services: list[TXCService] = []
    for service_xml in section.findall("Service"):

        service_parsed = parse_service(service_xml)
        if service_parsed:

            services.append(service_parsed)
    log.info("Parsed TXC Services", count=len(services))
    return services
