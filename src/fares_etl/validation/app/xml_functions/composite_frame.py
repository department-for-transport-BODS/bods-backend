from lxml.etree import _Element  # type: ignore

from ..constants import (
    FAREFRAME_TYPE_OF_FRAME_REF_SUBSTRING,
    LENGTH_OF_OPERATOR,
    LENGTH_OF_PUBLIC_CODE,
    NAMESPACE,
    ORG_OPERATOR_ID_SUBSTRING,
    TYPE_OF_FRAME_METADATA_SUBSTRING,
    TYPE_OF_FRAME_REF_SUBSTRING,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute, extract_text


def check_composite_frame_valid_between(_context: None, composite_frames: _Element):
    """
    Check if ValidBetween and it's child are present in CompositeFrame
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

    xpath = "x:ValidBetween"
    valid_between = composite_frame.xpath(xpath, namespaces=NAMESPACE)

    if not valid_between:
        source_line_valid_between = composite_frame.sourceline
        response_details = XMLViolationDetail(
            source_line_valid_between,
            ErrorMessages.MESSAGE_OBSERVATION_COMPOSITE_FRAME_VALID_BETWEEN_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "string(x:FromDate)"
    from_date = valid_between[0].xpath(xpath, namespaces=NAMESPACE)

    if not from_date:
        source_line_from_date = valid_between[0].sourceline
        response_details = XMLViolationDetail(
            source_line_from_date,
            ErrorMessages.MESSAGE_OBSERVATION_COMPOSITE_FRAME_FROM_DATE,
        )
        response = response_details.__list__()
        return response

    return ""


def check_resource_frame_operator_name(_context: None, composite_frames: _Element):
    """
    Check if mandatory element 'Name' is missing from organisations in ResourceFrame
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

    xpath = "x:frames/x:ResourceFrame/x:organisations/x:Operator"
    operators = composite_frame.xpath(xpath, namespaces=NAMESPACE)

    for operator in operators:
        xpath = "string(x:Name)"
        name = operator.xpath(xpath, namespaces=NAMESPACE)

        if name:
            continue

        source_line_name = operator.sourceline
        response_details = XMLViolationDetail(
            source_line_name,
            ErrorMessages.MESSAGE_OBSERVATION_RESOURCE_FRAME_OPERATOR_NAME_MISSING,
        )
        response = response_details.__list__()
        return response

    return ""


def check_resource_frame_organisation_elements(
    _context: None, composite_frames: _Element
):
    """
    Check if mandatory element 'ResourceFrame' or it's child missing from CompositeFrame
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

    xpath = "x:frames/x:ResourceFrame/x:organisations"
    organisations = composite_frame.xpath(xpath, namespaces=NAMESPACE)

    if not organisations:
        xpath = "x:frames/x:ResourceFrame"
        resource_frame = composite_frame.xpath(xpath, namespaces=NAMESPACE)
        if not resource_frame:
            xpath = "x:frames"
            frames = composite_frame.xpath(xpath, namespaces=NAMESPACE)
            source_line_resource_frame = frames[0].sourceline
            response_details = XMLViolationDetail(
                source_line_resource_frame,
                ErrorMessages.MESSAGE_OBSERVATION_RESOURCE_FRAME_MISSING,
            )
            response = response_details.__list__()
            return response
        source_line_organisations = resource_frame[0].sourceline
        response_details = XMLViolationDetail(
            source_line_organisations,
            ErrorMessages.MESSAGE_OBSERVATION_RESOURCE_FRAME_ORG_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "x:Operator"
    operators = organisations[0].xpath(xpath, namespaces=NAMESPACE)

    if not operators:
        source_line_operators = organisations[0].sourceline
        response_details = XMLViolationDetail(
            source_line_operators,
            ErrorMessages.MESSAGE_OBSERVATION_RESOURCE_FRAME_OPERATOR_MISSING,
        )
        response = response_details.__list__()
        return response

    for operator in operators:
        try:
            operator_id = extract_attribute([operator], "id")
        except KeyError:
            sourceline_operator = operator.sourceline
            response_details = XMLViolationDetail(
                sourceline_operator,
                ErrorMessages.MESSAGE_OPERATORS_ID_MISSING,
            )
            response = response_details.__list__()
            return response

        if not (
            ORG_OPERATOR_ID_SUBSTRING in operator_id
            and len(operator_id) == LENGTH_OF_OPERATOR
        ):
            sourceline_operator = operator.sourceline
            response_details = XMLViolationDetail(
                sourceline_operator,
                ErrorMessages.MESSAGE_OBSERVATION_OPERATOR_ID,
            )
            response = response_details.__list__()
            return response

        xpath = "x:PublicCode"
        public_code = operator.xpath(xpath, namespaces=NAMESPACE)

        if not public_code:
            source_line_public_code = operator.sourceline
            response_details = XMLViolationDetail(
                source_line_public_code,
                ErrorMessages.MESSAGE_OBSERVATION_RESOURCE_FRAME_PUBLIC_CODE_MISSING,
            )
            response = response_details.__list__()
            return response

        public_code_value = extract_text(public_code)

        if len(public_code_value) != LENGTH_OF_PUBLIC_CODE:
            sourceline_public_code = public_code[0].sourceline
            response_details = XMLViolationDetail(
                sourceline_public_code,
                ErrorMessages.MESSAGE_OBSERVATION_PUBLIC_CODE_LENGTH,
            )
            response = response_details.__list__()
            return response

    return ""


def check_value_of_type_of_frame_ref(_context: None, composite_frames: _Element):
    """
    Check if TypeOfFrameRef has either UK_PI_LINE_FARE_OFFER or
    UK_PI_NETWORK_FARE_OFFER in it.
    """
    is_frame_ref_value_valid = False
    composite_frame = composite_frames[0]

    try:
        composite_frame_id = extract_attribute(composite_frames, "id", "")
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

    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = composite_frame.xpath(xpath, namespaces=NAMESPACE)

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_ref, "ref", "")
    except KeyError:
        sourceline = type_of_frame_ref[0].sourceline
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_TYPE_OF_FRAME_REF_MISSING,
        )
        response = response_details.__list__()
        return response

    for ref_value in TYPE_OF_FRAME_REF_SUBSTRING:
        if ref_value in type_of_frame_ref_ref:
            is_frame_ref_value_valid = True

    if is_frame_ref_value_valid:
        return ""

    sourceline_composite_frame = type_of_frame_ref[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_composite_frame,
        ErrorMessages.MESSAGE_OBSERVATION_COMPOSITE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING,
    )
    response = response_details.__list__()
    return response


def check_type_of_frame_ref_ref(_context: None, composite_frames: _Element):
    """
    Check if FareFrame TypeOfFrameRef has either UK_PI_FARE_PRODUCT or
    UK_PI_FARE_PRICE in it.
    """
    is_frame_ref_value_valid = False
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

    xpath = "x:frames/x:FareFrame"
    fare_frames = composite_frame.xpath(xpath, namespaces=NAMESPACE)

    for fare_frame in fare_frames:
        xpath = "x:TypeOfFrameRef"
        type_of_frame_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)
        if type_of_frame_ref:
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
            for ref_value in FAREFRAME_TYPE_OF_FRAME_REF_SUBSTRING:
                if ref_value in type_of_frame_ref_ref:
                    is_frame_ref_value_valid = True

    if is_frame_ref_value_valid:
        return ""

    sourceline_fare_frame = composite_frame.sourceline
    response_details = XMLViolationDetail(
        sourceline_fare_frame,
        ErrorMessages.MESSAGE_OBSERVATION_TYPE_OF_FARE_FRAME_REF_MISSING,
    )
    response = response_details.__list__()
    return response
