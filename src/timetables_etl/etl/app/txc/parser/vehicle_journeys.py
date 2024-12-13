"""
Vehicle Journey  XML Parsing
"""

from typing import cast, get_args

from lxml.etree import _Element
from structlog.stdlib import get_logger

from ..models.txc_types import CommercialBasisT, TimeDemandT
from ..models.txc_vehicle_journey import (
    TXCLayoverPoint,
    TXCVehicleJourney,
    TXCVehicleJourneyStopUsageStructure,
    TXCVehicleJourneyTimingLink,
)
from ..models.txc_vehicle_journey_common import (
    TXCBlock,
    TXCOperational,
    TXCTicketMachine,
)
from ..models.txc_vehicle_journey_flexible import TXCFlexibleVehicleJourney
from .operating_profile import parse_operating_profile
from .utils import find_section
from .utils_attributes import (
    parse_creation_datetime,
    parse_modification,
    parse_modification_datetime,
    parse_revision_number,
)
from .utils_tags import get_element_text, get_element_texts
from .vehicle_journeys_flexible import parse_flexible_vehicle_journey

log = get_logger()


def parse_vehicle_journey_stop_usage(
    stop_usage_xml: _Element,
) -> TXCVehicleJourneyStopUsageStructure | None:
    """
    Parse VehicleJourneyStopUsageStructure (From/To) section
    """
    wait_time = get_element_text(stop_usage_xml, "WaitTime")
    dynamic_destination_display = get_element_text(
        stop_usage_xml, "DynamicDestinationDisplay"
    )
    activity = get_element_text(stop_usage_xml, "Activity")

    if not any([wait_time, dynamic_destination_display, activity]):
        return None

    return TXCVehicleJourneyStopUsageStructure(
        WaitTime=wait_time,
        DynamicDestinationDisplay=dynamic_destination_display,
    )


def parse_vehicle_journey_timing_link(
    timing_link_xml: _Element,
) -> TXCVehicleJourneyTimingLink:
    """
    Parse VehicleJourneyTimingLink section
    """
    link_id = timing_link_xml.get("id")
    from_xml = timing_link_xml.find("From")
    from_stop_usage = (
        parse_vehicle_journey_stop_usage(from_xml) if from_xml is not None else None
    )

    to_xml = timing_link_xml.find("To")
    to_stop_usage = (
        parse_vehicle_journey_stop_usage(to_xml) if to_xml is not None else None
    )

    timing_link_ref = get_element_text(timing_link_xml, "JourneyPatternTimingLinkRef")
    if timing_link_ref is None:
        log.error(
            "PTI Requires JourneyPatternTimingLinkRef setting to UNKNOWN", id=link_id
        )
        timing_link_ref = "UNKNOWN"
    run_time = get_element_text(timing_link_xml, "RunTime")
    if run_time is None:
        log.warning("Missing VehicleJourneyTimingLink RunTime", id=link_id)
    return TXCVehicleJourneyTimingLink(
        id=link_id,
        JourneyPatternTimingLinkRef=timing_link_ref,
        VehicleJourneyRef=get_element_text(timing_link_xml, "VehicleJourneyRef"),
        RunTime=run_time,
        From=from_stop_usage,
        To=to_stop_usage,
        DutyCrewCode=get_element_text(timing_link_xml, "DutyCrewCode"),
    )


def parse_vehicle_journey_timing_links(
    vehicle_journey_xml: _Element,
) -> list[TXCVehicleJourneyTimingLink]:
    """
    Parse all VehicleJourneyTimingLink sections
    """
    timing_links = []
    for timing_link_xml in vehicle_journey_xml.findall("VehicleJourneyTimingLink"):
        timing_link = parse_vehicle_journey_timing_link(timing_link_xml)
        if timing_link is not None:
            timing_links.append(timing_link)
    return timing_links


def parse_operational(operational_xml: _Element) -> TXCOperational | None:
    """
    VehicleJourney->Operational
    """
    ticket_machine_xml = operational_xml.find("TicketMachine")
    ticket_machine = None
    if ticket_machine_xml is not None:
        journey_code = get_element_text(ticket_machine_xml, "JourneyCode")
        ticket_machine = TXCTicketMachine(JourneyCode=journey_code)

    block_xml = operational_xml.find("Block")
    block = None
    if block_xml is not None:
        description = get_element_text(block_xml, "Description")
        if description is not None:
            block_number = get_element_text(block_xml, "BlockNumber")
            block = TXCBlock(Description=description, BlockNumber=block_number)

    if ticket_machine is None and block is None:
        return None

    return TXCOperational(
        TicketMachine=ticket_machine,
        Block=block,
    )


def parse_layover_point(layover_point_xml: _Element) -> TXCLayoverPoint | None:
    """
    Parse Layover point section
    """
    duration = get_element_text(layover_point_xml, "Duration")
    name = get_element_text(layover_point_xml, "Name")
    location = get_element_text(layover_point_xml, "Location")

    if not duration or not name or not location:
        return None

    return TXCLayoverPoint(
        Duration=duration,
        Name=name,
        Location=location,
    )


def parse_sequence_number(vehicle_journey_xml: _Element) -> str | None:
    """
    Required Vehicle Journey Field
    """
    sequence_number = get_element_text(vehicle_journey_xml, "SequenceNumber")

    return sequence_number


def parse_operator_ref(vehicle_journey_xml: _Element) -> str | None:
    """
    Required Vehicle Journey Field
    """
    operator_ref = get_element_text(vehicle_journey_xml, "OperatorRef")

    return operator_ref


def parse_departure_time(vehicle_journey_xml: _Element) -> str | None:
    """
    Required Vehicle Journey Field
    """
    departure_time = get_element_text(vehicle_journey_xml, "DepartureTime")
    if not departure_time:
        log.warning("VehicleJourney missing required DepartureTime. Skipping.")
    return departure_time


def parse_vehicle_journey(vehicle_journey_xml: _Element) -> TXCVehicleJourney | None:
    """
    Vehicle Journey XML parsing
    """
    operator_ref = parse_operator_ref(vehicle_journey_xml)
    departure_time = parse_departure_time(vehicle_journey_xml)

    if not departure_time:
        log.warning(
            "Vehicle Journey missing departure time",
            xml=vehicle_journey_xml,
        )
        return None

    operational_xml = vehicle_journey_xml.find("Operational")
    operational = (
        parse_operational(operational_xml) if operational_xml is not None else None
    )

    operating_profile_xml = vehicle_journey_xml.find("OperatingProfile")
    operating_profile = (
        parse_operating_profile(operating_profile_xml)
        if operating_profile_xml is not None
        else None
    )

    time_demand: TimeDemandT | None = (
        cast(TimeDemandT, text)
        if (text := get_element_text(vehicle_journey_xml, "TimeDemand"))
        in get_args(TimeDemandT)
        else None
    )

    commercial_basis: CommercialBasisT = (
        cast(CommercialBasisT, text)
        if (text := get_element_text(vehicle_journey_xml, "CommercialBasis"))
        in get_args(CommercialBasisT)
        else "notContracted"
    )

    layover_point_xml = vehicle_journey_xml.find("LayoverPoint")
    layover_point = (
        parse_layover_point(layover_point_xml)
        if layover_point_xml is not None
        else None
    )

    departure_day_shift = get_element_text(vehicle_journey_xml, "DepartureDayShift")
    departure_day_shift = departure_day_shift if departure_day_shift == "+1" else None

    return TXCVehicleJourney(
        CreationDateTime=parse_creation_datetime(vehicle_journey_xml),
        ModificationDateTime=parse_modification_datetime(vehicle_journey_xml),
        Modification=parse_modification(vehicle_journey_xml),
        RevisionNumber=parse_revision_number(vehicle_journey_xml),
        PrivateCode=get_element_text(vehicle_journey_xml, "PrivateCode"),
        DestinationDisplay=get_element_text(vehicle_journey_xml, "DestinationDisplay"),
        OperatorRef=operator_ref,
        Operational=operational,
        OperatingProfile=operating_profile,
        TimeDemand=time_demand,
        CommercialBasis=commercial_basis,
        LayoverPoint=layover_point,
        GarageRef=get_element_texts(vehicle_journey_xml, "GarageRef"),
        Description=get_element_text(vehicle_journey_xml, "Description"),
        VehicleJourneyCode=get_element_text(vehicle_journey_xml, "VehicleJourneyCode"),
        ServiceRef=get_element_text(vehicle_journey_xml, "ServiceRef"),
        LineRef=get_element_text(vehicle_journey_xml, "LineRef"),
        JourneyPatternRef=get_element_text(vehicle_journey_xml, "JourneyPatternRef"),
        VehicleJourneyRef=get_element_text(vehicle_journey_xml, "VehicleJourneyRef"),
        Note=get_element_text(vehicle_journey_xml, "Note"),
        DepartureTime=departure_time,
        DepartureDayShift=departure_day_shift,
        VehicleJourneyTimingLink=parse_vehicle_journey_timing_links(
            vehicle_journey_xml
        ),
    )


def parse_vehicle_journeys(
    xml_data: _Element,
) -> list[TXCVehicleJourney | TXCFlexibleVehicleJourney]:
    """
    Parse XML for both regular and flexible Vehicle Journeys
    Returns a combined list of both journey types
    """
    section: _Element = find_section(xml_data, "VehicleJourneys")
    if section is None:
        return []

    journeys: list[TXCVehicleJourney | TXCFlexibleVehicleJourney] = []

    for vehicle_journey_xml in section.findall("VehicleJourney"):
        vehicle_journey = parse_vehicle_journey(vehicle_journey_xml)
        if vehicle_journey:
            journeys.append(vehicle_journey)

    for flexible_journey_xml in section.findall("FlexibleVehicleJourney"):
        flexible_journey = parse_flexible_vehicle_journey(flexible_journey_xml)
        if flexible_journey:
            journeys.append(flexible_journey)

    log.info(
        "Parsed TXC Vehicle Journeys",
        regular_count=len([j for j in journeys if isinstance(j, TXCVehicleJourney)]),
        flexible_count=len(
            [j for j in journeys if isinstance(j, TXCFlexibleVehicleJourney)]
        ),
    )

    return journeys
