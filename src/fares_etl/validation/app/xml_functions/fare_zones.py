from lxml.etree import _Element  # type: ignore

from ..constants import (
    NAMESPACE,
    TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING,
    TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute


def is_fare_zones_present_in_fare_frame(_context: None, fare_zones: _Element):
    """
    Check if fareZones is present in FareFrame.
    If true, then fareZones properties should be present
    """
    if not fare_zones:
        return ""

    xpath = "../x:TypeOfFrameRef"
    type_of_frame_ref = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_ref:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""
    if not (
        TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING in type_of_frame_ref_ref
        or TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING in type_of_frame_ref_ref
    ):
        sourceline_type_of_frame_ref = type_of_frame_ref[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_type_of_frame_ref,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING,
        )
        response = response_details.__list__()
        return response
    xpath = "x:FareZone"
    zones = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)

    if zones:
        return ""

    sourceline_fare_zone = fare_zones[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_fare_zone,
        ErrorMessages.MESSAGE_OBSERVATION_FARE_ZONE_MISSING,
    )
    response = response_details.__list__()
    return response


def is_name_present_in_fare_frame(_context: None, fare_zones: _Element):
    """
    Check if fareZones is present in FareFrame.
    If true, then fareZones properties should be present
    """
    if not fare_zones:
        return ""

    xpath = "../x:TypeOfFrameRef"
    type_of_frame_ref = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_ref:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return ""
    if not (
        TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING in type_of_frame_ref_ref
        or TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING in type_of_frame_ref_ref
    ):
        sourceline_type_of_frame_ref = type_of_frame_ref[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_type_of_frame_ref,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "//x:FareZone"
    zones = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)

    for zone in zones:
        xpath = "string(x:Name)"
        name = zone.xpath(xpath, namespaces=NAMESPACE)
        if not name:
            sourceline_zone = zone.sourceline
            response_details = XMLViolationDetail(
                sourceline_zone,
                ErrorMessages.MESSAGE_OBSERVATION_FARE_ZONES_NAME_MISSING,
            )
            response = response_details.__list__()
            return response

    return ""
