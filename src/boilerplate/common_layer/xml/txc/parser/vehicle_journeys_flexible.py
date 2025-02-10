"""
Parse Vehicle Journeys
"""

from typing import cast

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import (
    get_element_text,
    parse_creation_datetime,
    parse_modification,
    parse_modification_datetime,
    parse_revision_number,
)
from ..models import (
    DirectionT,
    TXCFlexibleServiceTimes,
    TXCFlexibleVehicleJourney,
    TXCServicePeriod,
)

log = get_logger()


def parse_flexible_service_times(
    flexible_times_xml: _Element,
) -> list[TXCFlexibleServiceTimes] | None:
    """
    Parse FlexibleServiceTimes section which can contain either
    ServicePeriod or AllDayService
    """

    service_times: list[TXCFlexibleServiceTimes] = []

    # Process children in document order
    for child in flexible_times_xml:
        if child.tag == "AllDayService":
            service_times.append(TXCFlexibleServiceTimes(AllDayService=True))
        elif child.tag == "ServicePeriod":
            start_time = get_element_text(child, "StartTime")
            if not start_time:
                log.warning("ServicePeriod missing StartTime")
                return None

            end_time = get_element_text(child, "EndTime")
            if not end_time:
                log.warning("ServicePeriod missing EndTime")
                return None

            service_times.append(
                TXCFlexibleServiceTimes(
                    ServicePeriod=TXCServicePeriod(
                        StartTime=start_time, EndTime=end_time
                    )
                )
            )

    if not service_times:
        log.warning(
            "FlexibleServiceTimes contains neither AllDayService nor ServicePeriod"
        )
        return None

    return service_times


def parse_flexible_vehicle_journey(
    flexible_journey_xml: _Element,
) -> TXCFlexibleVehicleJourney | None:
    """
    Parse FlexibleVehicleJourney XML section
    """
    vehicle_journey_code = get_element_text(flexible_journey_xml, "VehicleJourneyCode")
    if not vehicle_journey_code:
        log.warning("FlexibleVehicleJourney missing VehicleJourneyCode")
        return None

    service_ref = get_element_text(flexible_journey_xml, "ServiceRef")
    if not service_ref:
        log.warning("FlexibleVehicleJourney missing ServiceRef")
        return None

    line_ref = get_element_text(flexible_journey_xml, "LineRef")
    if not line_ref:
        log.warning("FlexibleVehicleJourney missing LineRef")
        return None

    flexible_times_xml = flexible_journey_xml.find("FlexibleServiceTimes")
    if flexible_times_xml is None:
        log.warning("FlexibleVehicleJourney missing FlexibleServiceTimes element")
        return None

    flexible_service_times = parse_flexible_service_times(flexible_times_xml)
    if not flexible_service_times:
        log.warning("FlexibleVehicleJourney has invalid FlexibleServiceTimes")
        return None

    direction: DirectionT | None = None
    direction_text = get_element_text(flexible_journey_xml, "Direction")
    if direction_text and direction_text != "":
        direction = cast(DirectionT, direction_text)

    # Build the model with known valid required fields
    return TXCFlexibleVehicleJourney(
        VehicleJourneyCode=vehicle_journey_code,
        ServiceRef=service_ref,
        LineRef=line_ref,
        FlexibleServiceTimes=flexible_service_times,
        # Optional fields
        CreationDateTime=parse_creation_datetime(flexible_journey_xml),
        ModificationDateTime=parse_modification_datetime(flexible_journey_xml),
        Modification=parse_modification(flexible_journey_xml),
        RevisionNumber=parse_revision_number(flexible_journey_xml),
        PrivateCode=get_element_text(flexible_journey_xml, "PrivateCode"),
        DestinationDisplay=get_element_text(flexible_journey_xml, "DestinationDisplay"),
        Direction=direction,
        OperatorRef=get_element_text(flexible_journey_xml, "OperatorRef"),
        Description=get_element_text(flexible_journey_xml, "Description"),
        JourneyPatternRef=get_element_text(flexible_journey_xml, "JourneyPatternRef"),
        VehicleJourneyRef=get_element_text(flexible_journey_xml, "VehicleJourneyRef"),
        Note=get_element_text(flexible_journey_xml, "Note"),
    )
