"""
Serviced Org Operating Profile Parsing
"""

from common_layer.xml.txc.models import (
    TXCServicedOrganisationDays,
    TXCServicedOrganisationDayType,
)
from common_layer.xml.utils import get_element_texts
from lxml.etree import _Element


def parse_serviced_organisation_day_element(
    element_xml: _Element | None,
) -> TXCServicedOrganisationDays | None:
    """
    Parse a single WorkingDays/Holidays element into TXCServicedOrganisationDays
    """
    if element_xml is None:
        return None

    working_days_xml = element_xml.find("WorkingDays")
    holidays_xml = element_xml.find("Holidays")

    working_days = (
        get_element_texts(working_days_xml, "ServicedOrganisationRef")
        if working_days_xml is not None
        else []
    )
    holidays = (
        get_element_texts(holidays_xml, "ServicedOrganisationRef")
        if holidays_xml is not None
        else []
    )

    if not working_days and not holidays:
        return None

    return TXCServicedOrganisationDays(
        WorkingDays=working_days,
        Holidays=holidays,
    )


def parse_serviced_organisation_days(
    serviced_organisation_xml: _Element,
) -> TXCServicedOrganisationDayType | None:
    """
    VehicleJourney -> OperatingProfile -> ServicedOrganisationDayType
    Parse the serviced organisation day type from XML
    """
    days_of_operation: list[TXCServicedOrganisationDays] = []
    days_of_non_operation: list[TXCServicedOrganisationDays] = []

    days_of_operation_xml = serviced_organisation_xml.find("DaysOfOperation")
    operation_day = parse_serviced_organisation_day_element(days_of_operation_xml)
    if operation_day:
        days_of_operation.append(operation_day)

    days_of_non_operation_xml = serviced_organisation_xml.find("DaysOfNonOperation")
    non_operation_day = parse_serviced_organisation_day_element(
        days_of_non_operation_xml
    )
    if non_operation_day:
        days_of_non_operation.append(non_operation_day)

    if not days_of_operation and not days_of_non_operation:
        return None

    return TXCServicedOrganisationDayType(
        DaysOfOperation=days_of_operation,
        DaysOfNonOperation=days_of_non_operation,
    )
