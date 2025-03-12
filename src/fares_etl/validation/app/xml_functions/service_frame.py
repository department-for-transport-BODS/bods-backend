# pylint: disable=too-many-return-statements,duplicate-code

"""
Service Frame
"""

from lxml.etree import _Element  # type: ignore

from ..constants import (
    NAMESPACE,
    STOP_POINT_ID_SUBSTRING,
    TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute


def check_lines_operator_ref_present(_context: None, lines: _Element):
    """
    Check ServiceFrame.lines.Line.OperatorRef is present
    """
    line = lines[0]
    xpath = "x:OperatorRef"
    operator_ref = line.xpath(xpath, namespaces=NAMESPACE)
    if operator_ref:
        return ""

    sourceline_line = line.sourceline
    response_details = XMLViolationDetail(
        sourceline_line,
        ErrorMessages.MESSAGE_OBSERVATION_OPERATORREF_MISSING,
    )
    response = response_details.__list__()
    return response


def check_lines_public_code_present(_context: None, lines: _Element):
    """
    Check ServiceFrame.lines.Line.PublicCode is present
    """
    line = lines[0]
    xpath = "string(x:PublicCode)"
    public_code = line.xpath(xpath, namespaces=NAMESPACE)

    if public_code:
        return ""

    sourceline_line = line.sourceline
    response_details = XMLViolationDetail(
        sourceline_line,
        ErrorMessages.MESSAGE_OBSERVATION_PUBLICCODE_MISSING,
    )
    response = response_details.__list__()
    return response


def is_lines_present_in_service_frame(_context: None, service_frame: _Element):
    """
    Check if ServiceFrame is present,
    corresponding Line properties should be present
    """
    if not service_frame:
        return ""

    xpath = "x:lines"
    lines = service_frame[0].xpath(xpath, namespaces=NAMESPACE)

    if not lines:
        return ""

    xpath = "x:Line"
    service_frame_line = lines[0].xpath(xpath, namespaces=NAMESPACE)

    if not service_frame_line:
        sourceline_line = lines[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_line,
            ErrorMessages.MESSAGE_OBSERVATION_LINE_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "string(x:Name)"
    name = service_frame_line[0].xpath(xpath, namespaces=NAMESPACE)

    if name:
        return ""

    sourceline_line = service_frame_line[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_line,
        ErrorMessages.MESSAGE_OBSERVATION_NAME_MISSING,
    )
    response = response_details.__list__()
    return response


def is_schedule_stop_points(_context: None, service_frame: _Element):
    """
    Check if ServiceFrame is present,
    corresponding scheduledStopPoints properties should be present
    """
    if not service_frame:
        return ""

    xpath = "x:scheduledStopPoints"
    schedule_stop_points = service_frame[0].xpath(xpath, namespaces=NAMESPACE)

    if not schedule_stop_points:
        return ""

    xpath = "x:ScheduledStopPoint"
    stop_points = schedule_stop_points[0].xpath(xpath, namespaces=NAMESPACE)

    if not stop_points:
        sourceline_stop_point = schedule_stop_points[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_stop_point,
            ErrorMessages.MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_MISSING,
        )
        response = response_details.__list__()

        return response

    for stop in stop_points:
        try:
            stop_id = extract_attribute([stop], "id")
        except KeyError:
            sourceline = stop.sourceline
            response_details = XMLViolationDetail(
                sourceline,
                ErrorMessages.MESSAGE_STOP_POINT_ATTR_ID_MISSING,
            )
            response = response_details.__list__()
            return response

        if STOP_POINT_ID_SUBSTRING not in stop_id:
            sourceline_stop_point = stop.sourceline
            response_details = XMLViolationDetail(
                sourceline_stop_point,
                ErrorMessages.MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_ID_FORMAT,
            )
            response = response_details.__list__()
            return response

        xpath = "string(x:Name)"
        name = stop.xpath(xpath, namespaces=NAMESPACE)

        if name:
            continue

        sourceline_stop_point = stop.sourceline
        response_details = XMLViolationDetail(
            sourceline_stop_point,
            ErrorMessages.MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_NAME_MISSING,
        )
        response = response_details.__list__()
        return response

    return ""


def is_service_frame_present(_context: None, service_frame: _Element):
    """
    Check if ServiceFrame is present in FareFrame.
    If true, TypeOfFrameRef should include UK_PI_NETWORK
    """
    if not service_frame:
        return ""

    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = service_frame[0].xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_ref:
        response_details = XMLViolationDetail(
            service_frame[0].sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_SERVICEFRAME_TYPE_OF_FRAME_REF_MISSING,
        )
        response = response_details.__list__()
        return response

    try:
        ref = extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        sourceline = type_of_frame_ref[0].sourceline
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_TYPE_OF_FRAME_REF_MISSING,
        )
        response = response_details.__list__()
        return response

    if TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING in ref:
        return ""

    sourceline_frame_ref = type_of_frame_ref[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_frame_ref,
        ErrorMessages.MESSAGE_OBSERVATION_SERVICEFRAME_TYPE_OF_FRAME_REF_MISSING,
    )
    response = response_details.__list__()
    return response
