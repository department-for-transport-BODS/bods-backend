from lxml.etree import _Element  # type: ignore

from ..constants import (
    FARE_STRUCTURE_ELEMENT_DURATION_REF,
    FARE_STRUCTURE_ELEMENT_TRAVEL_REF,
    NAMESPACE,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute


def _get_fare_structure_time_intervals(element: _Element):
    """
    Checks if the fareStructureElements properties are present
    """
    xpath = "x:timeIntervals"
    time_intervals = element.xpath(xpath, namespaces=NAMESPACE)

    if not time_intervals:
        sourceline = element.sourceline
        response_details = XMLViolationDetail(
            sourceline, ErrorMessages.MESSAGE_OBSERVATION_TIME_INTERVALS_MISSING
        )
        response = response_details.__list__()
        return response

    for element in time_intervals:
        xpath = "x:TimeIntervalRef"
        time_interval_ref = element.xpath(xpath, namespaces=NAMESPACE)

        if time_interval_ref:
            continue

        sourceline = element.sourceline
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_TIME_INTERVAL_REF_MISSING,
        )
        response = response_details.__list__()
        return response

    return ""


def _get_individual_tariff_time_interval(element: _Element):
    element = element[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)
    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:tariffs/x:Tariff/x:timeIntervals/x:TimeInterval"
    time_interval = element.xpath(xpath, namespaces=NAMESPACE)

    if time_interval:
        return ""

    xpath = "x:tariffs/x:Tariff/x:timeIntervals"
    intervals = element.xpath(xpath, namespaces=NAMESPACE)

    if not intervals:
        return ""

    sourceline_time_interval = intervals[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_time_interval,
        ErrorMessages.MESSAGE_OBSERVATION_TARIFF_TIME_INTERVAL_MISSING,
    )
    response = response_details.__list__()
    return response


def _get_tariff_time_interval_name(element: _Element):
    element = element[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)
    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:tariffs/x:Tariff/x:timeIntervals/x:TimeInterval"
    intervals = element.xpath(xpath, namespaces=NAMESPACE)

    for interval in intervals:
        xpath = "string(x:Name)"
        name = interval.xpath(xpath, namespaces=NAMESPACE)

        if name:
            continue

        sourceline_name = interval.sourceline
        response_details = XMLViolationDetail(
            sourceline_name,
            ErrorMessages.MESSAGE_OBSERVATION_TARIFF_NAME_MISSING,
        )
        response = response_details.__list__()
        return response

    return ""


def _get_tariff_time_intervals(element: _Element):
    """
    Checks if the tarrif element has timeIntervals
    """
    element = element[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)
    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:tariffs/x:Tariff/x:timeIntervals"
    time_intervals = element.xpath(xpath, namespaces=NAMESPACE)

    if time_intervals:
        return ""

    xpath = "x:tariffs/x:Tariff"
    tariff = element.xpath(xpath, namespaces=NAMESPACE)
    sourceline_time_intervals = tariff[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_time_intervals,
        ErrorMessages.MESSAGE_OBSERVATION_TARIFF_TIME_INTERVALS_MISSING,
    )
    response = response_details.__list__()
    return response


def _get_generic_parameter_assignment_properties(element: _Element):
    """
    Checks if the FareStructureElement.GenericParameterAssignment properties are present
    """
    xpath = "x:GenericParameterAssignment"
    generic_parameter_assignment = element.xpath(xpath, namespaces=NAMESPACE)
    if not generic_parameter_assignment:
        sourceline_generic_parameter = element.sourceline
        response_details = XMLViolationDetail(
            sourceline_generic_parameter,
            ErrorMessages.MESSAGE_OBSERVATION_GENERIC_PARAMETER,
        )
        response = response_details.__list__()
        return response
    xpath = "x:limitations"
    limitations = generic_parameter_assignment[0].xpath(xpath, namespaces=NAMESPACE)

    if not limitations:
        sourceline = generic_parameter_assignment[0].sourceline
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_GENERIC_PARAMETER_LIMITATION,
        )
        response = response_details.__list__()
        return response

    for limitation in limitations:
        xpath = "x:RoundTrip"
        round_trip = limitation.xpath(xpath, namespaces=NAMESPACE)
        if not round_trip:
            sourceline = limitation.sourceline
            response_details = XMLViolationDetail(
                sourceline, ErrorMessages.MESSAGE_OBSERVATION_ROUND_TRIP_MISSING
            )
            response = response_details.__list__()
            return response
        xpath = "x:TripType"
        trip_type = round_trip[0].xpath(xpath, namespaces=NAMESPACE)
        if not trip_type:
            sourceline = round_trip[0].sourceline
            response_details = XMLViolationDetail(
                sourceline, ErrorMessages.MESSAGE_OBSERVATION_TRIP_TYPE_MISSING
            )
            response = response_details.__list__()
            return response

    return ""


def is_fare_structure_element_present(_context: None, fare_frames: _Element):
    """
    Check if ProductType is dayPass or periodPass.
    If true, FareStructureElement elements
    should be present in Tariff.FareStructureElements
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if product_type not in ["dayPass", "periodPass"]:
        return ""

    xpath = "x:tariffs/x:Tariff/x:fareStructureElements/x:FareStructureElement"
    fare_structure_element = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    for element in fare_structure_element:
        xpath = "x:TypeOfFareStructureElementRef"
        fare_structure_ref = element.xpath(xpath, namespaces=NAMESPACE)
        try:
            fare_structure_ref_ref = extract_attribute(fare_structure_ref, "ref")
        except KeyError:
            return ""

        if fare_structure_ref_ref == FARE_STRUCTURE_ELEMENT_DURATION_REF:
            return _get_fare_structure_time_intervals(element)

    return ""


def is_generic_parameter_limitations_present(_context: None, fare_frames: _Element):
    """
    Check if ProductType is singleTrip, dayReturnTrip, periodReturnTrip.
    If true, FareStructureElement.GenericParameterAssignment elements
    should be present in Tariff.FareStructureElements
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    xpath = "x:tariffs/x:Tariff/x:fareStructureElements/x:FareStructureElement"
    fare_structure_elements = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    for fare_structure_element in fare_structure_elements:
        xpath = "x:TypeOfFareStructureElementRef"
        type_of_frame_ref = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)
        try:
            type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            return ""
        if (
            type_of_frame_ref_ref == FARE_STRUCTURE_ELEMENT_TRAVEL_REF
            and product_type in ["singleTrip", "dayReturnTrip", "periodReturnTrip"]
        ):
            return _get_generic_parameter_assignment_properties(fare_structure_element)

    return ""


def is_individual_time_interval_present_in_tariffs(
    _context: None, fare_frames: _Element
):
    """
    Check if ProductType is dayPass or periodPass.
    If true, timeIntervals element should be present in tarrifs
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    return (
        _get_individual_tariff_time_interval(fare_frames)
        if product_type in ["dayPass", "periodPass"]
        else ""
    )


def is_time_interval_name_present_in_tariffs(_context: None, fare_frames: _Element):
    """
    Check if ProductType is dayPass or periodPass.
    If true, timeIntervals element should be present in tarrifs
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    return (
        _get_tariff_time_interval_name(fare_frames)
        if product_type in ["dayPass", "periodPass"]
        else ""
    )


def is_time_intervals_present_in_tarrifs(_context: None, fare_frames: _Element):
    """
    Check if ProductType is dayPass or periodPass.
    If true, timeIntervals element should be present in tarrifs
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    return (
        _get_tariff_time_intervals(fare_frames)
        if product_type in ["dayPass", "periodPass"]
        else ""
    )
