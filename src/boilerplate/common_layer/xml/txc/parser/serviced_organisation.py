"""
Serviced Organisation Section Parsing
"""

from typing import cast

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import (
    find_section,
    get_elem_bool_default,
    get_element_date,
    get_element_text,
    parse_creation_datetime,
    parse_modification,
    parse_modification_datetime,
    parse_revision_number,
    parse_xml_attribute,
)
from ..models import (
    TXCServicedOrganisation,
    TXCServicedOrganisationAnnotatedNptgLocalityRef,
    TXCServicedOrganisationDatePattern,
)
from ..models.txc_types import ServiceOrganisationClassificationT, StatusT

log = get_logger()


def parse_date_range(
    date_range_xml: _Element,
) -> TXCServicedOrganisationDatePattern | None:
    """
    Parse a single ServicedOrganisationDatePattern element
    """
    start_date = get_element_date(date_range_xml, "StartDate")
    end_date = get_element_date(date_range_xml, "EndDate")

    if not start_date or not end_date:
        log.warning("Date Range is missing required Start Date  or End Date, skipping")
        return None
    return TXCServicedOrganisationDatePattern(
        StartDate=start_date,
        EndDate=end_date,
        Description=get_element_text(date_range_xml, "Description"),
        Provisional=get_elem_bool_default(date_range_xml, "Provisional", False),
    )


def parse_date_ranges(
    date_ranges_xml: _Element,
) -> list[TXCServicedOrganisationDatePattern] | None:
    """
    Parse list of DateRange elements
    Returns None if no date ranges were parsed
    """
    date_ranges: list[TXCServicedOrganisationDatePattern] = []
    for date_range in date_ranges_xml.findall("DateRange"):
        parsed_range = parse_date_range(date_range)
        if parsed_range is not None:
            date_ranges.append(parsed_range)
    return date_ranges if date_ranges else None


def parse_working_days(
    org_xml: _Element,
) -> list[TXCServicedOrganisationDatePattern] | None:
    """Parse WorkingDays section of a serviced organisation"""
    working_days_xml = org_xml.find("WorkingDays")
    if working_days_xml is None:
        return None
    return parse_date_ranges(working_days_xml)


def parse_holidays(
    org_xml: _Element,
) -> list[TXCServicedOrganisationDatePattern] | None:
    """Parse Holidays section of a serviced organisation"""
    holidays_xml = org_xml.find("Holidays")
    if holidays_xml is None:
        return None
    return parse_date_ranges(holidays_xml)


def parse_annotated_locality(
    org_xml: _Element,
) -> TXCServicedOrganisationAnnotatedNptgLocalityRef | None:
    """Parse AnnotatedNptgLocalityRef section"""
    locality_xml = org_xml.find("AnnotatedNptgLocalityRef")
    if locality_xml is None:
        return None
    locality_ref = get_element_text(locality_xml, "NptgLocalityRef")
    if locality_ref is None:
        log.warning(
            "AnnotatedNptgLocalityRef given but required NptgLocalityRef missing"
        )
        return None
    return TXCServicedOrganisationAnnotatedNptgLocalityRef(
        NptgLocalityRef=locality_ref,
        LocalityName=get_element_text(locality_xml, "LocalityName"),
        LocalityQualifier=get_element_text(locality_xml, "LocalityQualifier"),
    )


def parse_status(tag: _Element) -> StatusT | None:
    """
    Parse Status attribute into StatusT enum
    """
    status = parse_xml_attribute(tag, "Status")
    if status and status in ["active", "inactive", "pending"]:
        return cast(StatusT, status)
    return None


def parse_serviced_organisation(org_xml: _Element) -> TXCServicedOrganisation | None:
    """
    Parse a single serviced organisation
    """
    org_code = get_element_text(org_xml, "OrganisationCode")
    if org_code is None:
        log.warning("Servied Organisation is missing Organisation Code")
        return None

    return TXCServicedOrganisation(
        # Attributes
        CreationDateTime=parse_creation_datetime(org_xml),
        ModificationDateTime=parse_modification_datetime(org_xml),
        Modification=parse_modification(org_xml),
        RevisionNumber=parse_revision_number(org_xml),
        Status=parse_status(org_xml),
        # Elements
        OrganisationCode=org_code,
        PrivateCode=get_element_text(org_xml, "PrivateCode"),
        Name=get_element_text(org_xml, "Name"),
        ServicedOrganisationClassification=cast(
            ServiceOrganisationClassificationT,
            parse_xml_attribute(org_xml, "ServicedOrganisationClassification"),
        ),
        WorkingDays=parse_working_days(org_xml),
        Holidays=parse_holidays(org_xml),
        ParentServicedOrganisationRef=get_element_text(
            org_xml, "ParentServicedOrganisationRef"
        ),
        AdministrativeAreaRef=get_element_text(org_xml, "AdministrativeAreaRef"),
        AnnotatedNptgLocalityRef=parse_annotated_locality(org_xml),
        LocalEducationAuthorityRef=get_element_text(
            org_xml, "LocalEducationAuthorityRef"
        ),
    )


def parse_serviced_organisations(xml_data: _Element) -> list[TXCServicedOrganisation]:
    """
    Parse ServicedOrganisations Section of TXC XML
    """
    try:
        section = find_section(xml_data, "ServicedOrganisations")
    except ValueError:
        return []

    orgs: list[TXCServicedOrganisation] = []
    for org_xml in section.findall("ServicedOrganisation"):
        org_parsed = parse_serviced_organisation(org_xml)
        if org_parsed:
            orgs.append(org_parsed)
    log.info("Parsed Serviced Organisations", count=len(orgs))
    return orgs
