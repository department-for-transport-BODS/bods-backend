from lxml.etree import _Element  # type: ignore

from ..constants import (
    NAMESPACE,
    TYPE_OF_FRAME_FARE_TABLES_REF_SUBSTRING,
    TYPE_OF_FRAME_METADATA_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    TYPE_OF_FRAME_REF_RESOURCE_FRAME_SUBSTRING,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute


def check_fare_frame_type_of_frame_ref_present_fare_price(
    _context: None, fare_frames: _Element
):
    """
    Check if mandatory element 'TypeOfFrameRef' and
    'UK_PI_FARE_PRICE' ref is present
    """
    fare_frame = fare_frames[0]
    try:
        fare_frame_id = extract_attribute(fare_frames, "id")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_FARE_TABLES_REF_SUBSTRING not in fare_frame_id:
        return ""

    sourceline_fare_frame = fare_frame.sourceline
    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_ref:
        response_details = XMLViolationDetail(
            sourceline_fare_frame,
            ErrorMessages.MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_ELEMENT_MISSING,
        )
        response = response_details.__list__()
        return response

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_FARE_TABLES_REF_SUBSTRING in type_of_frame_ref_ref:
        return ""

    sourceline_type_of_frame_ref = type_of_frame_ref[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_type_of_frame_ref,
        ErrorMessages.MESSAGE_OBSERVATION_TYPE_OF_FARE_FRAME_REF_INCORRECT,
    )
    response = response_details.__list__()
    return response


def check_fare_frame_type_of_frame_ref_present_fare_product(
    _context: None, fare_frames: _Element
):
    """
    Check if mandatory element 'TypeOfFrameRef'
    and 'UK_PI_FARE_PRODUCT' ref is present
    """
    fare_frame = fare_frames[0]
    try:
        fare_frame_id = extract_attribute(fare_frames, "id")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in fare_frame_id:
        return ""

    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_ref:
        sourceline_fare_frame = fare_frame.sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_frame,
            ErrorMessages.MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_ELEMENT_FARE_PRODUCT_MISSING,
        )
        response = response_details.__list__()
        return response

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref:
        return ""

    sourceline_type_of_frame_ref = type_of_frame_ref[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_type_of_frame_ref,
        ErrorMessages.MESSAGE_OBSERVATION_TYPE_OF_FARE_FRAME_REF_FARE_PRODUCT_INCORRECT,
    )
    response = response_details.__list__()
    return response


def check_resource_frame_type_of_frame_ref_present(
    _context: None, composite_frames: _Element
):
    """
    Check if mandatory element 'TypeOfFrameRef' is present in 'ResourceFrame'
    and 'UK_PI_COMMON' ref is present
    """
    composite_frame = composite_frames[0]
    try:
        composite_frame_id = extract_attribute(composite_frames, "id")
    except KeyError:
        sourceline = composite_frame.sourceline
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_COMPOSITE_FRAME_ID_MISSING,
        )
        response = response_details.__list__()
        return response

    if TYPE_OF_FRAME_METADATA_SUBSTRING in composite_frame_id:
        return ""

    xpath = "x:frames/x:ResourceFrame"
    resource_frame = composite_frame.xpath(xpath, namespaces=NAMESPACE)
    try:
        resource_frame_id = extract_attribute(resource_frame, "id")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_RESOURCE_FRAME_SUBSTRING not in resource_frame_id:
        return ""

    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = resource_frame[0].xpath(xpath, namespaces=NAMESPACE)
    if not type_of_frame_ref:
        sourceline_resource_frame = resource_frame[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_resource_frame,
            ErrorMessages.MESSAGE_OBSERVATION_RESOURCE_FRAME_TYPE_OF_FRAME_REF_ELEMENT_MISSING,
        )
        response = response_details.__list__()
        return response

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        sourceline = type_of_frame_ref[0].sourceline
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_TYPE_OF_FRAME_REF_MISSING,
        )
        response = response_details.__list__()
        return response

    if TYPE_OF_FRAME_REF_RESOURCE_FRAME_SUBSTRING in type_of_frame_ref_ref:
        return ""

    sourceline_type_of_frame_ref = type_of_frame_ref[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_type_of_frame_ref,
        ErrorMessages.MESSAGE_OBSERVATION_RESOURCE_FRAME_TYPE_OF_FARE_FRAME_REF_INCORRECT,
    )
    response = response_details.__list__()
    return response
