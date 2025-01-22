"""
Validator Helper functions
"""

import re
from datetime import UTC, datetime
from typing import Union

from common_layer.database.client import SqlDB
from common_layer.database.repos import NaptanStopPointRepo
from dateutil import parser
from lxml import etree
from lxml.etree import _Element
from structlog.stdlib import get_logger

from .destination_display import DestinationDisplayValidator
from .lines import LinesValidator
from .stop_point import StopPointValidator

log = get_logger()

ElementsOrStr = Union[list[etree.Element], list[str], str]
PROHIBITED_CHARS = r",[]{}^=@:;#$£?%+<>«»\/|~_¬"


def _extract_text(elements, default=None) -> str | None:
    text = ""
    if isinstance(elements, list) and len(elements) > 0:
        item = elements[0]
        if isinstance(item, str):
            text = item
        else:
            text = getattr(item, "text")
    elif isinstance(elements, str):
        text = elements
    elif hasattr(elements, "text"):
        text = getattr(elements, "text")
    else:
        text = default
    return text


def cast_to_date(_context, date) -> float:
    """
    Casts a lxml date element to an int.
    """
    text = _extract_text(date) or ""
    return parser.parse(text).timestamp()


def cast_to_bool(_context, elements: ElementsOrStr) -> bool:
    """
    Casts either a list of str, list of Elements or a str to a boolean
    """
    text = _extract_text(elements, default="false")
    return text == "true"


def to_days(_context, days, *_args) -> float:
    """Returns number of days as number of seconds."""
    return days * 24 * 60 * 60.0


def contains_date(_context, text) -> bool:
    """
    Determines if the input text contains any date-like strings.
    """
    text = _extract_text(text) or ""
    for word in text.split():
        try:
            if word.isdigit():
                continue
            parser.parse(word)
        except parser.ParserError:
            pass
        else:
            return True
    return False


def check_flexible_service_timing_status(_context, flexiblejourneypatterns) -> bool:
    """
    Examines XML journey pattern data and verifies that in cases where
    both fixed and flexible stops are present in the same sequence, all fixed stops
    have a timing status of "otherPoint".
    """
    log.info(
        "Validation Start: Flexible Service Timing Status",
    )
    timing_status_value_list = []
    flexiblejourneypattern = flexiblejourneypatterns[0]
    ns = {"x": flexiblejourneypattern.nsmap.get(None)}
    stop_points_in_seq_list = flexiblejourneypattern.xpath(
        "x:StopPointsInSequence", namespaces=ns
    )
    for stop_points_in_seq in stop_points_in_seq_list:
        fixed_stop_usage_list = stop_points_in_seq.xpath(
            "x:FixedStopUsage", namespaces=ns
        )
        flexible_stop_usage_list = stop_points_in_seq.xpath(
            "x:FlexibleStopUsage", namespaces=ns
        )

        if len(fixed_stop_usage_list) > 0 and len(flexible_stop_usage_list) > 0:
            for fixed_stop_usage in fixed_stop_usage_list:
                timing_status_value_list.append(
                    _extract_text(
                        fixed_stop_usage.xpath("x:TimingStatus", namespaces=ns), ""
                    )
                )

    result = all(
        timing_status_value == "otherPoint"
        for timing_status_value in timing_status_value_list
    )
    return result


def validate_non_naptan_stop_points(_context, points: list[_Element]) -> bool:
    """
    Runs the StopPointValidator
    """
    log.info(
        "Validation Start: Non Naptan Stop Points",
    )
    point = points[0]
    validator = StopPointValidator(point)
    return validator.validate()


def get_stop_point_ref_list(stop_points, ns) -> list[str]:
    """
    For each stop point in the input, the function looks for FlexibleStopUsage elements
    and extracts their StopPointRef values.
    """
    stop_point_ref_list: list[str] = []
    for flex_stop_point in stop_points:
        flexible_stop_usage_list = flex_stop_point.xpath(
            "x:FlexibleStopUsage", namespaces=ns
        )
        if len(flexible_stop_usage_list) > 0:
            for flexible_stop_usage in flexible_stop_usage_list:
                ref = _extract_text(
                    flexible_stop_usage.xpath("x:StopPointRef", namespaces=ns), None
                )
                if ref is not None:
                    stop_point_ref_list.append(ref)
                else:
                    log.warning(
                        "Missing StopPointRef in FlexibleStopUsage",
                        flexible_stop_usage=flexible_stop_usage,
                    )

    return stop_point_ref_list


def get_flexible_service_stop_point_ref_validator(db: SqlDB):
    """
    Creates a validator function that checks if all flexible service stop points are
    properly registered in the NAPTAN database as flexible bus stops.
    """

    def check_flexible_service_stop_point_ref(_context, flexiblejourneypatterns):
        log.info(
            "Validation Start: Check Flexible Service Stop Point Ref",
        )
        atco_codes_list = []
        flexiblejourneypattern = flexiblejourneypatterns[0]
        ns = {"x": flexiblejourneypattern.nsmap.get(None)}
        stop_points_in_seq_list = flexiblejourneypattern.xpath(
            "x:StopPointsInSequence", namespaces=ns
        )
        stop_points_in_flexzone_list = flexiblejourneypattern.xpath(
            "x:FlexibleZones", namespaces=ns
        )
        atco_codes_list = list(
            set(
                get_stop_point_ref_list(stop_points_in_seq_list, ns)
                + get_stop_point_ref_list(stop_points_in_flexzone_list, ns)
            )
        )
        repo = NaptanStopPointRepo(db)
        total_compliant = repo.get_count(
            atco_codes=atco_codes_list, bus_stop_type="FLX", stop_type="BCT"
        )

        return total_compliant == len(atco_codes_list)

    return check_flexible_service_stop_point_ref


def check_inbound_outbound_description(_context, services):
    """
    Check when file has detected a standard service (includes StandardService):
        - If both InboundDescription and OutboundDescription are not present, return False.
        - All other combinations are acceptable, return True.
    """
    log.info(
        "Validation Start: Check Inbound / Outbound Description",
    )
    for service in services:
        ns = {"x": service.nsmap.get(None)}
        standard_service_list = service.xpath(
            "x:Service/x:StandardService", namespaces=ns
        )
        if standard_service_list:
            inbound_description_list = service.xpath(
                "x:Service/x:Lines/x:Line/x:InboundDescription", namespaces=ns
            )
            outbound_description_list = service.xpath(
                "x:Service/x:Lines/x:Line/x:OutboundDescription", namespaces=ns
            )
            if (
                len(inbound_description_list) == 0
                and len(outbound_description_list) == 0
            ):
                return False

        return True


def check_description_for_inbound_description(_context, services: list) -> bool:
    """
    Check if a StandardService has description present for InboundDescription.

    Args:
        context: The context for the check.
        services: A list of service elements to be checked.

    Returns:
        bool: True if all services have descriptions for InboundDescription, False otherwise.
    """
    log.info(
        "Validation Start: Description for Inbound Description",
    )
    for service in services:
        inbound_description_list = []
        ns = {"x": service.nsmap.get(None)}
        standard_service_list = service.xpath(
            "x:Service/x:StandardService", namespaces=ns
        )
        if standard_service_list:
            inbound_description_list = service.xpath(
                "x:Service/x:Lines/x:Line/x:InboundDescription", namespaces=ns
            )
        for inbound_description_tag in inbound_description_list:
            if len(inbound_description_tag.xpath("x:Description", namespaces=ns)) == 0:
                return False
        return True
    return False


def check_description_for_outbound_description(_context, services: list):
    """
    Check if a StandardService has description present for OutboundDescription.

    Args:
        context: The context for the check.
        services: A list of service elements to be checked.

    Returns:
        bool: True if all services have descriptions for OutboundDescription, False otherwise.
    """
    log.info(
        "Validation Start: Description for Outbound Description",
    )
    for service in services:
        outbound_description_tag = []
        ns = {"x": service.nsmap.get(None)}
        standard_service_list = service.xpath(
            "x:Service/x:StandardService", namespaces=ns
        )
        if standard_service_list:
            outbound_description_list = service.xpath(
                "x:Service/x:Lines/x:Line/x:OutboundDescription", namespaces=ns
            )
            for outbound_description_tag in outbound_description_list:
                if (
                    len(outbound_description_tag.xpath("x:Description", namespaces=ns))
                    == 0
                ):
                    return False
        return True


def check_flexible_service_times(_context, vehiclejourneys) -> bool:
    """
    Check when FlexibleVehicleJourney is present, that FlexibleServiceTimes
    is also present at least once. If not present at all, then return False.
    """
    log.info(
        "Validation Start: Check Flexible Service Times",
    )
    ns = {"x": vehiclejourneys[0].nsmap.get(None)}
    flexible_vehiclejourneys = vehiclejourneys[0].xpath(
        "x:FlexibleVehicleJourney", namespaces=ns
    )
    if flexible_vehiclejourneys:
        for flexible_journey in flexible_vehiclejourneys:
            flexible_service_times = flexible_journey.xpath(
                "x:FlexibleServiceTimes", namespaces=ns
            )
            if len(flexible_service_times) == 0:
                return False

            return True
    return False


def has_destination_display(_context, patterns):
    """
    First check if DestinationDisplay in JourneyPattern is provided.

    If not, we need to check in if DynamicDestinationDisplay is provided for
    each stop inside a JourneyPatternTimingLink.

    If both conditions above fail, then DestinationDisplay should
    mandatory nside VehicleJourney.
    """
    log.info(
        "Validation Start: Has Destination Display",
    )
    pattern = patterns[0]
    validator = DestinationDisplayValidator(pattern)
    return validator.validate()


def has_name(_context, elements, *args) -> bool:
    """
    Checks if elements are in the list of names.
    """
    if not isinstance(elements, list):
        elements = [elements]

    for el in elements:
        namespaces = {"x": el.nsmap.get(None)}
        local_name = el.xpath("local-name()", namespaces=namespaces)
        if local_name not in args:
            return False
    return True


def has_flexible_or_standard_service(_context, services) -> bool:
    """
    If it is a non-flexible service (flexible service is not defined),
    then it should have a StandardService defined. If validation fails,
    then a validation issue should be recorded in validation report.
    """
    log.info(
        "Validation Start: Has Flexible or Standard Service",
    )
    for service in services:
        ns = {"x": service.nsmap.get(None)}
        service_classification = service.xpath(
            "x:ServiceClassification/x:Flexible", namespaces=ns
        )

        if service_classification:
            flexible_service_list = service.xpath("x:FlexibleService", namespaces=ns)
            if flexible_service_list:
                return True
            return False
        standard_service_list = service.xpath("x:StandardService", namespaces=ns)
        return bool(standard_service_list)

    return False


def has_flexible_service_classification(_context, services: list) -> bool:
    """
    Check when file has detected a flexible service (includes
    FlexibleService), it has ServiceClassification and Flexible elements.
    If the file also has a standard service, then return True.
    """
    log.info(
        "Validation Start: Has Flexible Service Classification",
    )
    for service in services:
        ns = {"x": service.nsmap.get(None)}
        flexible_service_list = service.xpath("x:FlexibleService", namespaces=ns)

        if not flexible_service_list:
            return True

        service_classification_list = service.xpath(
            "x:ServiceClassification", namespaces=ns
        )
        if not service_classification_list:
            return False

        for service_classification in service_classification_list:
            if service_classification.xpath("x:Flexible", namespaces=ns):
                return True

        return False
    return False


def has_prohibited_chars(_context, element: _Element) -> bool:
    """
    Check if Element has disallowed XML characters
    """
    log.info(
        "Validation Start: Prohibited Characters",
    )
    chars = _extract_text(element) or ""
    return len([c for c in chars if c in PROHIBITED_CHARS]) > 0


def check_service_group_validations(_context, services):
    """
    Enforces the following rules:
    1. A service group can contain exactly one service of any type, OR
    2. A service group can contain multiple services ONLY IF:
       - It contains exactly one registered flexible service
       - It contains NO registered standard services

    The function categorizes services into:
    - Registered StandardService (ServiceCode format: XX9999999:*)
    - Unregistered StandardService (ServiceCode format: UZ[A-Z0-9]{7}:*)
    - Registered FlexibleService (ServiceCode matches registered format + has Flexible)
    """
    log.info(
        "Validation Start: Service Group Validations",
        count=len(services),
    )
    services = services[0]
    ns = {"x": services.nsmap.get(None)}
    service_list = services.xpath("x:Service", namespaces=ns)
    registered_code_regex = re.compile("[a-zA-Z]{2}\\d{7}:[a-zA-Z0-9]+$")
    unregistered_code_regex = re.compile("UZ[a-zA-Z0-9]{7}:[a-zA-Z0-9]+$")

    registered_standard_service = len(
        list(
            filter(
                lambda s: registered_code_regex.match(
                    s.xpath("string(x:ServiceCode)", namespaces=ns)
                )
                and s.xpath("x:StandardService", namespaces=ns),
                service_list,
            )
        )
    )
    unregistered_services = len(
        list(
            filter(
                lambda s: unregistered_code_regex.match(
                    s.xpath("string(x:ServiceCode)", namespaces=ns)
                ),
                service_list,
            )
        )
    )
    registered_flexible_service = len(
        list(
            filter(
                lambda s: registered_code_regex.match(
                    s.xpath("string(x:ServiceCode)", namespaces=ns)
                )
                and s.xpath("x:ServiceClassification/x:Flexible", namespaces=ns),
                service_list,
            )
        )
    )

    total_services = (
        registered_standard_service
        + registered_flexible_service
        + unregistered_services
    )

    # More than one services are allowed only when there is a registered flexible service.
    # If there is a registered standard service then no other service types should be present
    if total_services == 1 or (
        total_services > 1
        and registered_flexible_service == 1
        and registered_standard_service == 0
    ):
        return True

    return False


def is_member_of(_context, element, *args) -> bool:
    """
    Checks if the text content of an element is a member of the provided arguments
    """
    text = _extract_text(element, default="")
    return text in args


def regex(_context, element, pattern) -> bool:
    """
    Checks if element's text content matches the provided regular expression pattern
    """
    chars = _extract_text(element) or ""
    return re.match(pattern, chars) is not None


def strip(_context, text) -> str:
    """
    Removes leading and trailing whitespace from element's text content
    """
    text = _extract_text(text) or ""
    return text.strip()


def today(_context) -> float:
    """
    Gets current UTC date as a Unix timestamp
    """
    now = datetime.now(UTC).date().isoformat()
    date = parser.parse(now)
    return date.timestamp()


def validate_line_id(_context, lines):
    """
    Validates that Line@id has the correct format.
    """
    log.info(
        "Validation Start: Line ID",
        count=len(lines),
    )
    line = lines[0]
    ns = {"x": line.nsmap.get(None)}

    xpath = "string(@id)"
    line_id = line.xpath(xpath, namespaces=ns)

    xpath = "string(//x:Operators/x:Operator/x:NationalOperatorCode)"
    noc = line.xpath(xpath, namespaces=ns)

    xpath = "string(../../x:ServiceCode)"
    service_code = line.xpath(xpath, namespaces=ns)

    xpath = "string(x:LineName)"
    line_name = line.xpath(xpath, namespaces=ns)
    line_name = line_name.replace(" ", "")

    expected_line_id = f"{noc}:{service_code}:{line_name}"
    return line_id.startswith(expected_line_id)


def validate_modification_date_time(_context, roots):
    log.info(
        "Validation Start: Modification Datetime",
        count=len(roots),
    )
    root = roots[0]
    modification_date = root.attrib.get("ModificationDateTime")
    creation_date = root.attrib.get("CreationDateTime")
    revision_number = root.attrib.get("RevisionNumber")

    if revision_number == "0":
        return modification_date == creation_date
    else:
        return creation_date < modification_date


def validate_licence_number(_context, elements: list[etree._Element]) -> bool:
    """
    Validate the license number within a list of XML elements if Primary Mode is not coach.

    This function checks if the PrimaryMode is not "coach", then LicenceNumber is mandatory and should be non-empty.

    Args:
        context: The context in which the function is called.
        elements (list): A list of XML elements to validate

    Returns:
        bool: True if all elements are valid according to the specified rules,
              False otherwise.
    """
    log.info(
        "Validation Start: Licence Number",
        count=len(elements),
    )
    ns = {"x": elements[0].nsmap.get(None)}
    for element in elements:
        primary_mode = element.xpath(
            ".//x:PrimaryMode", namespaces=ns  # pyright: ignore
        )
        licence_number = element.xpath(
            ".//x:LicenceNumber", namespaces=ns  # pyright: ignore
        )

        if primary_mode and primary_mode[0].text.lower() == "coach":
            continue
        elif not (licence_number and licence_number[0].text):
            return False
    return True


def has_servicedorganisation_working_days(_context, service_organisations):
    """
    Checks if all service organisations have defined working days.

    This function iterates over a list of service organisations and verifies
    whether each organisation has defined working days by checking the
    corresponding XML structure. If any service organisation lacks working
    days, the function returns False; otherwise, it returns True.

    Args:
        context: The context in which the function is called (not used in the
                 current implementation but may be relevant for future use).
        service_organisations (list): A list of service organisation objects
                                       that are expected to contain XML
                                       elements.

    Returns:
        bool: True if all service organisations have working days defined,
              False otherwise.

    """
    log.info(
        "Validation Start: Serviced Organisation Working Days",
        count=len(service_organisations),
    )
    is_valid = True
    for service_organisation in service_organisations:
        ns = {"x": service_organisation.nsmap.get(None)}
        working_days = service_organisation.xpath("x:WorkingDays", namespaces=ns)
        if not working_days:
            is_valid = False
    return is_valid


def get_lines_validator(db: SqlDB):
    def validate_lines(_context, lines_list: list[etree._Element]) -> bool:
        log.info(
            "Validation Start: Lines",
            lines_count=len(lines_list),
        )
        lines = lines_list[0]
        repo = NaptanStopPointRepo(db)
        stop_area_map = repo.get_stop_area_map()
        validator = LinesValidator(lines, stop_area_map=stop_area_map)
        return validator.validate()

    return validate_lines
