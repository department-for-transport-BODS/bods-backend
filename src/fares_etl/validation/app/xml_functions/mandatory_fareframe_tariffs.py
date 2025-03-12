# pylint: disable=duplicate-code


"""
Fare Frame Tariffs
"""

from lxml.etree import _Element  # type: ignore

from ..constants import (
    NAMESPACE,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    TYPE_OF_TARIFF_REF_STRING,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute


def check_tariff_basis(_context: None, elements: _Element):
    """
    Checks if 'ref' of element 'TypeOfFrameRef' is correct and
    if 'TariffBasis' element is present within 'Tariff'
    """
    element = elements[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)
    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:TariffBasis"
    tariff_basis = element.xpath(xpath, namespaces=NAMESPACE)
    if tariff_basis:
        return ""

    sourceline = element.sourceline
    response_details = XMLViolationDetail(
        sourceline,
        ErrorMessages.MESSAGE_OBSERVATION_TARIFF_TARIFF_BASIS_MISSING,
    )
    response = response_details.__list__()
    return response


def check_tariff_operator_ref(_context: None, elements: _Element):
    """
    Checks if 'ref' of element 'TypeOfFrameRef' is correct and
    if 'OperatorRef' element is present within 'Tariff'
    """
    element = elements[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:OperatorRef"
    operator_ref = element.xpath(xpath, namespaces=NAMESPACE)
    xpath = "x:GroupOfOperatorsRef"
    multi_operator_ref = element.xpath(xpath, namespaces=NAMESPACE)

    if not (operator_ref or multi_operator_ref):
        sourceline = element.sourceline
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_TARIFF_OPERATOR_REF_MISSING,
        )
        response = response_details.__list__()
        return response

    if not multi_operator_ref:
        return ""

    xpath = """
        ../../../x:ResourceFrame/x:groupsOfOperators/x:GroupOfOperators/x:members/x:OperatorRef
    """
    members = element.xpath(xpath, namespaces=NAMESPACE)
    if len(members) >= 2:
        return ""

    xpath = "../../../x:ResourceFrame/x:groupsOfOperators/x:GroupOfOperators"
    groups_of_operators = element.xpath(xpath, namespaces=NAMESPACE)
    sourceline_groups_of_operators = groups_of_operators[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_groups_of_operators,
        ErrorMessages.MESSAGE_OBSERVATION_MISSING_MULTI_OPERATOR_REFS,
    )
    response = response_details.__list__()
    return response


def check_tariff_validity_conditions(_context: None, elements: _Element):
    """
    Checks if 'ref' of element 'TypeOfFrameRef' is correct and
    if 'ValidityConditions', 'ValidBetween' and 'FromDate'
    are present within 'Tariff'
    """
    element = elements[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)
    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:validityConditions"
    validity_conditions = element.xpath(xpath, namespaces=NAMESPACE)

    if not validity_conditions:
        validity_conditions_sourceline = element.sourceline
        response_details = XMLViolationDetail(
            validity_conditions_sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_TARIFF_VALIDITY_CONDITIONS_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "x:ValidBetween"
    valid_between = validity_conditions[0].xpath(xpath, namespaces=NAMESPACE)

    if not valid_between:
        valid_between_sourceline = validity_conditions[0].sourceline
        response_details = XMLViolationDetail(
            valid_between_sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_TARIFF_VALID_BETWEEN_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "string(x:FromDate)"
    from_date = valid_between[0].xpath(xpath, namespaces=NAMESPACE)

    if from_date:
        return ""

    from_date_sourceline = valid_between[0].sourceline
    response_details = XMLViolationDetail(
        from_date_sourceline,
        ErrorMessages.MESSAGE_OBSERVATION_TARIFF_FROM_DATE_MISSING,
    )
    response = response_details.__list__()
    return response


def check_type_of_tariff_ref_values(_context: None, elements: _Element):
    """
    Checks if 'ref' of element 'TypeOfFrameRef' is correct and
    if 'TypeOfTariffRef' element has acceptable 'ref' values
    """
    element = elements[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)
    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:TypeOfTariffRef"
    is_type_of_tariff_ref = element.xpath(xpath, namespaces=NAMESPACE)
    if not is_type_of_tariff_ref:
        sourceline = element.sourceline
        response_details = XMLViolationDetail(
            sourceline, ErrorMessages.MESSAGE_OBSERVATION_TARIFF_REF_MISSING
        )
        response = response_details.__list__()
        return response

    try:
        type_of_tariff_ref_ref = extract_attribute(is_type_of_tariff_ref, "ref")
    except KeyError:
        sourceline = is_type_of_tariff_ref[0].sourceline
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_TYPE_OF_TARIFF_REF_MISSING,
        )
        response = response_details.__list__()
        return response

    if type_of_tariff_ref_ref in TYPE_OF_TARIFF_REF_STRING:
        return ""

    sourceline = is_type_of_tariff_ref[0].sourceline
    response_details = XMLViolationDetail(
        sourceline, ErrorMessages.MESSAGE_OBSERVATION_INCORRECT_TARIFF_REF
    )
    response = response_details.__list__()
    return response
