from lxml.etree import _Element  # type: ignore

from ..constants import (
    FARE_STRUCTURE_ACCESS_RIGHT_ELIGIBILITY_REF,
    FARE_STRUCTURE_ACCESS_RIGHT_REF,
    FARE_STRUCTURE_ACCESS_RIGHT_TRAVEL_REF,
    FARE_STRUCTURE_ELEMENT_ACCESS_REF,
    FARE_STRUCTURE_ELEMENT_ELIGIBILITY_REF,
    FARE_STRUCTURE_ELEMENT_TRAVEL_REF,
    NAMESPACE,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute, find_indices


def _get_fare_structure_element(fare_structure_elements: _Element):
    """
    Gets the fare structure element
    """
    fare_structure_element = fare_structure_elements[0]
    xpath = "//x:FareStructureElement"
    return fare_structure_element.xpath(xpath, namespaces=NAMESPACE)


def _get_type_of_fare_structure_element_ref(fare_structure_element: _Element):
    """
    Gets the type of fare structure element ref
    """
    return fare_structure_element.xpath(
        "x:TypeOfFareStructureElementRef", namespaces=NAMESPACE
    )


def _get_access_right_assignment_ref(fare_structure_element: _Element):
    """
    Gets the access right assignment ref
    """
    return fare_structure_element.xpath(
        "x:GenericParameterAssignment/x:TypeOfAccessRightAssignmentRef",
        namespaces=NAMESPACE,
    )


def check_frequency_of_use(_context: None, fare_structure_elements: _Element):
    """
    Check if mandatory element 'FrequencyOfUse' or it's child missing in
    FareStructureElement with TypeOfFareStructureElementRef - fxc:travel_conditions
    """
    fare_structure_element = fare_structure_elements[0]
    xpath = "x:TypeOfFareStructureElementRef"
    type_of_frame_refs = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if FARE_STRUCTURE_ELEMENT_TRAVEL_REF != type_of_frame_ref_ref:
        return ""

    xpath = "x:GenericParameterAssignment/x:limitations/x:FrequencyOfUse"
    frequency_of_use = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

    if not frequency_of_use:
        xpath = "x:GenericParameterAssignment/x:limitations"
        limitations = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)
        if limitations:
            sourceline_fare_structure_element = limitations[0].sourceline
        else:
            sourceline_fare_structure_element = fare_structure_element.sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_structure_element,
            ErrorMessages.MESSAGE_OBSERVATION_GENERIC_PARAMETER_FREQUENCY_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = """
        string(x:GenericParameterAssignment/x:limitations/x:FrequencyOfUse/x:FrequencyOfUseType)
    """
    frequency_of_use_type = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

    if not frequency_of_use_type:
        sourceline_use_type = frequency_of_use[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_use_type,
            ErrorMessages.MESSAGE_OBSERVATION_GENERIC_PARAMETER_FREQUENCY_TYPE_MISSING,
        )
        response = response_details.__list__()
        return response

    return ""


def check_generic_parameters_for_access(_context: None, elements: _Element):
    """
    Checks if 'GenericParameterAssignment' has acceptable elements within it when
    'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'
    """
    element = elements[0]
    xpath = "x:FareStructureElement"
    fare_structure_elements = element.xpath(xpath, namespaces=NAMESPACE)

    for fare_structure_element in fare_structure_elements:
        xpath = "x:TypeOfFareStructureElementRef"
        type_of_fare_structure_element_ref = fare_structure_element.xpath(
            xpath, namespaces=NAMESPACE
        )

        try:
            type_of_fare_structure_element_ref_ref = extract_attribute(
                type_of_fare_structure_element_ref, "ref"
            )
        except KeyError:
            return ""

        if type_of_fare_structure_element_ref_ref != FARE_STRUCTURE_ELEMENT_ACCESS_REF:
            continue

        xpath = "x:GenericParameterAssignment"
        generic_parameter = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

        if not generic_parameter:
            sourceline_generic_parameter = fare_structure_element.sourceline
            response_details = XMLViolationDetail(
                sourceline_generic_parameter,
                ErrorMessages.MESSAGE_OBSERVATION_GENERIC_PARAMETER,
            )
            response = response_details.__list__()
            return response

        xpath = "x:TypeOfAccessRightAssignmentRef"
        access_right_assignment = generic_parameter[0].xpath(
            xpath, namespaces=NAMESPACE
        )

        if not access_right_assignment:
            sourceline_access_right_assignment = generic_parameter[0].sourceline
            response_details = XMLViolationDetail(
                sourceline_access_right_assignment,
                ErrorMessages.MESSAGE_OBSERVATION_ACCESS_RIGHT_ASSIGNMENT,
            )
            response = response_details.__list__()
            return response

    return ""


def check_type_of_fare_structure_element_ref(
    _context: None, fare_structure_element: _Element
):
    """
    Checks the type of fare structure element reference.
    """
    element = fare_structure_element[0]
    type_of_fare_structure_element_ref = _get_type_of_fare_structure_element_ref(
        element
    )
    sourceline = element.sourceline
    if type_of_fare_structure_element_ref:
        return ""

    response_details = XMLViolationDetail(
        sourceline, ErrorMessages.MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT_REF
    )
    response = response_details.__list__()
    return response


def check_validity_parameter_for_access(
    _context: None, generic_parameter_assignments: _Element
):
    """
    Checks if 'GenericParameterAssignment' has 'validityParameters'
    elements within it when 'TypeOfFareStructureElementRef' has
    a ref value of 'fxc:access'
    """
    generic_parameter_assignment = generic_parameter_assignments[0]
    xpath = "../x:TypeOfFareStructureElementRef"
    type_of_fare_structure_element_ref = generic_parameter_assignment.xpath(
        xpath, namespaces=NAMESPACE
    )

    try:
        type_of_fare_structure_element_ref_ref = extract_attribute(
            type_of_fare_structure_element_ref, "ref"
        )
    except KeyError:
        return ""

    if FARE_STRUCTURE_ELEMENT_ACCESS_REF != type_of_fare_structure_element_ref_ref:
        return ""

    generic_parameter_assignment = generic_parameter_assignments[0]
    xpath = "x:validityParameters"
    validity_parameters = generic_parameter_assignment.xpath(
        xpath, namespaces=NAMESPACE
    )
    if validity_parameters:
        return ""

    sourceline_generic_parameter = generic_parameter_assignment.sourceline
    response_details = XMLViolationDetail(
        sourceline_generic_parameter,
        ErrorMessages.MESSAGE_OBSERVATION_VALIDITY_PARAMETER,
    )
    response = response_details.__list__()
    return response


def check_validity_grouping_type_for_access(
    _context: None, generic_parameter_assignments: _Element
):
    """
    Checks if 'GenericParameterAssignment' has either 'ValidityParameterGroupingType'
    or 'ValidityParameterAssignmentType' elements within it when
    'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'
    """
    generic_parameter_assignment = generic_parameter_assignments[0]
    xpath = "../x:TypeOfFareStructureElementRef"
    type_of_fare_structure_element_ref = generic_parameter_assignment.xpath(
        xpath, namespaces=NAMESPACE
    )

    try:
        type_of_fare_structure_element_ref_ref = extract_attribute(
            type_of_fare_structure_element_ref, "ref"
        )
    except KeyError:
        return ""

    if FARE_STRUCTURE_ELEMENT_ACCESS_REF != type_of_fare_structure_element_ref_ref:
        return ""

    xpath = "string(x:ValidityParameterGroupingType)"
    grouping_type = generic_parameter_assignment.xpath(xpath, namespaces=NAMESPACE)

    xpath = "string(x:ValidityParameterAssignmentType)"
    assignment_type = generic_parameter_assignment.xpath(xpath, namespaces=NAMESPACE)

    if grouping_type or assignment_type:
        return ""

    sourceline_generic_parameter = generic_parameter_assignment.sourceline
    response_details = XMLViolationDetail(
        sourceline_generic_parameter,
        ErrorMessages.MESSAGE_OBSERVATION_VALIDITY_GROUPING_PARAMETER,
    )
    response = response_details.__list__()
    return response


def check_generic_parameters_for_eligibility(_context: None, elements: _Element):
    """
    Checks if 'GenericParameterAssignment' has acceptable elements within it when
    'TypeOfFareStructureElementRef' has a ref value of 'fxc:eligibility'
    """
    element = elements[0]
    xpath = "x:FareStructureElement"
    fare_structure_elements = element.xpath(xpath, namespaces=NAMESPACE)

    for fare_structure_element in fare_structure_elements:
        xpath = "x:TypeOfFareStructureElementRef"
        type_of_fare_structure_element_ref = fare_structure_element.xpath(
            xpath, namespaces=NAMESPACE
        )
        try:
            type_of_fare_structure_element_ref_ref = extract_attribute(
                type_of_fare_structure_element_ref, "ref"
            )
        except KeyError:
            return ""

        if (
            FARE_STRUCTURE_ELEMENT_ELIGIBILITY_REF
            != type_of_fare_structure_element_ref_ref
        ):
            continue

        generic_parameter = fare_structure_element.xpath(
            "x:GenericParameterAssignment", namespaces=NAMESPACE
        )

        if not generic_parameter:
            sourceline_generic_parameter = fare_structure_element.sourceline
            response_details = XMLViolationDetail(
                sourceline_generic_parameter,
                ErrorMessages.MESSAGE_OBSERVATION_GENERIC_PARAMETER,
            )
            response = response_details.__list__()
            return response

        limitations = generic_parameter[0].xpath("x:limitations", namespaces=NAMESPACE)

        if not limitations:
            sourceline_limitations = generic_parameter[0].sourceline
            response_details = XMLViolationDetail(
                sourceline_limitations,
                ErrorMessages.MESSAGE_OBSERVATION_GENERIC_PARAMETER_LIMITATION,
            )
            response = response_details.__list__()
            return response

        xpath = "x:UserProfile"
        user_profile = limitations[0].xpath(xpath, namespaces=NAMESPACE)

        if not user_profile:
            sourceline_user_profile = limitations[0].sourceline
            response_details = XMLViolationDetail(
                sourceline_user_profile,
                ErrorMessages.MESSAGE_OBSERVATION_GENERIC_PARAMETER_LIMITATIONS_USER,
            )
            response = response_details.__list__()
            return response

        xpath = "string(x:Name)"
        user_profile_name = user_profile[0].xpath(xpath, namespaces=NAMESPACE)
        xpath = "string(x:UserType)"
        user_type = user_profile[0].xpath(xpath, namespaces=NAMESPACE)

        if not (user_profile_name and user_type):
            sourceline = user_profile[0].sourceline
            response_details = XMLViolationDetail(
                sourceline,
                ErrorMessages.MESSAGE_OBSERVATION_GENERIC_PARAMETER_ELIGIBILITY_PROPS_MISSING,
            )
            response = response_details.__list__()
            return response

    return ""


def check_fare_structure_element(_context: None, fare_structure_elements: _Element):
    """
    Checks if the fare structure elements are valid.
    """
    all_fare_structure_elements = _get_fare_structure_element(fare_structure_elements)
    sourceline = fare_structure_elements[0].sourceline
    if all_fare_structure_elements:
        return ""

    response_details = XMLViolationDetail(
        sourceline, ErrorMessages.MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT
    )
    response = response_details.__list__()
    return response


def all_fare_structure_element_checks(
    _context: None, fare_structure_elements: _Element
):
    """
    1st Check: Check 'FareStructureElement' appears minimum 3 times.

    2nd Check - If 'TypeOfAccessRightAssignmentRef' and 'TypeOfFareStructureElementRef'
    elements have the correct combination of 'ref' values:

    fxc:access and fxc:can_access,
    fxc:eligibility and fxc:eligible,
    fxc:travel_conditions and fxc:condition_of_use
    """
    list_type_of_fare_structure_element_ref_ref: list[str] = []
    list_type_of_access_right_assignment_ref_ref: list[str] = []
    sourceline = fare_structure_elements[0].sourceline

    all_fare_structure_elements = _get_fare_structure_element(fare_structure_elements)
    length_all_fare_structure_elements = len(all_fare_structure_elements)

    try:
        if length_all_fare_structure_elements <= 2:
            response_details = XMLViolationDetail(
                sourceline,
                ErrorMessages.MESSAGE_OBSERVATION_FARE_STRUCTURE_COMBINATIONS,
            )
            response = response_details.__list__()
            return response

        for element in all_fare_structure_elements:
            type_of_fare_structure_element_ref = (
                _get_type_of_fare_structure_element_ref(element)
            )

            try:
                type_of_fare_structure_element_ref_ref = extract_attribute(
                    type_of_fare_structure_element_ref, "ref"
                )
            except KeyError:
                response_details = XMLViolationDetail(
                    sourceline,
                    ErrorMessages.MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
                )
                response = response_details.__list__()
                return response

            list_type_of_fare_structure_element_ref_ref.append(
                type_of_fare_structure_element_ref_ref
            )
            type_of_access_right_assignment_ref = _get_access_right_assignment_ref(
                element
            )

            try:
                type_of_access_right_assignment_ref_ref = extract_attribute(
                    type_of_access_right_assignment_ref, "ref"
                )
            except KeyError:
                response_details = XMLViolationDetail(
                    sourceline,
                    ErrorMessages.MESSAGE_TYPE_OF_ACCESS_RIGHT_REF_MISSING,
                )
                response = response_details.__list__()
                return response

            list_type_of_access_right_assignment_ref_ref.append(
                type_of_access_right_assignment_ref_ref
            )

        access_index_set = find_indices(
            list_type_of_fare_structure_element_ref_ref,
            FARE_STRUCTURE_ELEMENT_ACCESS_REF,
        )
        can_access_index_set = find_indices(
            list_type_of_access_right_assignment_ref_ref,
            FARE_STRUCTURE_ACCESS_RIGHT_REF,
        )
        eligibility_index_set = find_indices(
            list_type_of_fare_structure_element_ref_ref,
            FARE_STRUCTURE_ELEMENT_ELIGIBILITY_REF,
        )
        eligibile_index_set = find_indices(
            list_type_of_access_right_assignment_ref_ref,
            FARE_STRUCTURE_ACCESS_RIGHT_ELIGIBILITY_REF,
        )
        travel_conditions_index_set = find_indices(
            list_type_of_fare_structure_element_ref_ref,
            FARE_STRUCTURE_ELEMENT_TRAVEL_REF,
        )
        condition_of_use_index_set = find_indices(
            list_type_of_access_right_assignment_ref_ref,
            FARE_STRUCTURE_ACCESS_RIGHT_TRAVEL_REF,
        )
    except ValueError:
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_STRUCTURE_COMBINATIONS,
        )
        response = response_details.__list__()
        return response

    can_access_count = len(access_index_set.intersection(can_access_index_set))
    eligibile_count = len(eligibility_index_set.intersection(eligibile_index_set))
    cond_of_use_count = len(
        travel_conditions_index_set.intersection(condition_of_use_index_set)
    )

    if can_access_count >= 1 and eligibile_count >= 1 and cond_of_use_count >= 1:
        return ""

    response_details = XMLViolationDetail(
        sourceline,
        ErrorMessages.MESSAGE_OBSERVATION_FARE_STRUCTURE_COMBINATIONS,
    )
    response = response_details.__list__()
    return response
