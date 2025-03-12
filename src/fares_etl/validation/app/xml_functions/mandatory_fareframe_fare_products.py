from lxml.etree import _Element  # type: ignore

from ..constants import (
    FARE_STRUCTURE_AMOUNT_OF_PRICE_UNIT_LABEL,
    FARE_STRUCTURE_PREASSIGNED_LABEL,
    NAMESPACE,
    TYPE_OF_AMOUNT_OF_PRICE_UNIT_PRODUCT_TYPE,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute


def _get_fare_product_label_name(fare_product: _Element):
    """
    Determines the label name for a given fare product element.
    """
    if FARE_STRUCTURE_AMOUNT_OF_PRICE_UNIT_LABEL in str(fare_product.tag):
        return FARE_STRUCTURE_AMOUNT_OF_PRICE_UNIT_LABEL

    return FARE_STRUCTURE_PREASSIGNED_LABEL


def check_access_right_elements(_context: None, fare_products: _Element):
    """
    Check if mandatory element 'AccessRightInProduct' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_product = fare_products[0]
    fare_product_label = _get_fare_product_label_name(fare_product)
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:accessRightsInProduct"
    access_right = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if not access_right:
        sourceline_preassigned = fare_product.sourceline
        response_details = XMLViolationDetail(
            sourceline_preassigned,
            ErrorMessages.MESSAGE_OBSERVATION_ACCESS_MISSING.format(fare_product_label),
        )
        response = response_details.__list__()
        return response

    xpath = "x:AccessRightInProduct/x:ValidableElementRef"
    validable_element_ref = access_right[0].xpath(xpath, namespaces=NAMESPACE)

    if validable_element_ref:
        return ""

    xpath = "x:AccessRightInProduct"
    child_access_right = access_right[0].xpath(xpath, namespaces=NAMESPACE)
    if not child_access_right:
        sourceline_validable_element_ref = access_right[0].sourceline
    sourceline_validable_element_ref = child_access_right[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_validable_element_ref,
        ErrorMessages.MESSAGE_OBSERVATION_ACCESS_VALIDABLE_MISSING,
    )
    response = response_details.__list__()
    return response


def check_fare_product_validable_elements(_context: None, fare_products: _Element):
    """
    Check if element 'validableElements' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_product = fare_products[0]
    fare_product_label = _get_fare_product_label_name(fare_product)
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:validableElements"
    validable_elements = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if not validable_elements:
        sourceline_fare_frame = fare_product.sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_frame,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_VALIDABLE_ELEMENTS_MISSING.format(
                fare_product_label
            ),
        )
        response = response_details.__list__()
        return response

    xpath = "x:ValidableElement"
    validable_element = validable_elements[0].xpath(xpath, namespaces=NAMESPACE)

    if not validable_element:
        sourceline_validable_element = validable_elements[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_validable_element,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_VALIDABLE_ELEMENT_MISSING.format(
                fare_product_label
            ),
        )
        response = response_details.__list__()
        return response

    xpath = "x:fareStructureElements"
    fare_structure_elements = validable_element[0].xpath(xpath, namespaces=NAMESPACE)

    if not fare_structure_elements:
        sourceline_fare_structure = validable_element[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_structure,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_VALIDABLE_FARE_MISSING.format(
                fare_product_label
            ),
        )
        response = response_details.__list__()
        return response

    xpath = "x:FareStructureElementRef"
    fare_structure_element_ref = fare_structure_elements[0].xpath(
        xpath, namespaces=NAMESPACE
    )

    if fare_structure_element_ref:
        return ""

    sourceline_fare_structure_ref = fare_structure_elements[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_fare_structure_ref,
        ErrorMessages.MESSAGE_OBSERVATION_FARE_VALIDABLE_FARE_REF_MISSING.format(
            fare_product_label
        ),
    )
    response = response_details.__list__()
    return response


def check_fare_products(_context: None, fare_frames: _Element):
    """
    Check if mandatory element 'PreassignedFareProduct' missing in fareProducts
    for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:fareProducts"
    fare_products = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if not fare_products:
        sourceline = fare_frame.sourceline
        response_details = XMLViolationDetail(
            sourceline,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING,
        )
        response = response_details.__list__()
        return response

    fare_product_label = FARE_STRUCTURE_PREASSIGNED_LABEL

    if len(fare_products) > 0 and fare_products[0].find(
        f"x:{FARE_STRUCTURE_AMOUNT_OF_PRICE_UNIT_LABEL}", namespaces=NAMESPACE
    ):
        fare_product_label = FARE_STRUCTURE_AMOUNT_OF_PRICE_UNIT_LABEL

    xpath = f"x:{fare_product_label}"
    fare_product = fare_products[0].xpath(xpath, namespaces=NAMESPACE)
    if not fare_product:
        sourceline_fare_product = fare_products[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_product,
            ErrorMessages.MESSAGE_OBSERVATION_FARE_MISSING.format(fare_product_label),
        )
        response = response_details.__list__()
        return response

    xpath = "string(x:Name)"
    name = fare_product[0].xpath(xpath, namespaces=NAMESPACE)

    if name:
        return ""

    sourceline_preassigned = fare_product[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_preassigned,
        ErrorMessages.MESSAGE_OBSERVATION_PRODUCT_FARE_NAME_MISSING.format(
            fare_product_label
        ),
    )
    response = response_details.__list__()
    return response


def check_fare_products_charging_type(_context: None, fare_products: _Element):
    """
    Check if mandatory element is 'ChargingMomentType' present in PreassignedFareProduct
    for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_product = fare_products[0]
    fare_product_label = _get_fare_product_label_name(fare_product)
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "string(x:ChargingMomentType)"
    charging_moment_type = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if charging_moment_type:
        return ""

    sourceline_preassigned = fare_product.sourceline
    response_details = XMLViolationDetail(
        sourceline_preassigned,
        ErrorMessages.MESSAGE_OBSERVATION_FARE_CHARGING_MISSING.format(
            fare_product_label
        ),
    )
    response = response_details.__list__()
    return response


def check_fare_products_type_ref(_context: None, fare_products: _Element):
    """
    Check if mandatory element is 'TypeOfFareProductRef' present
    in PreassignedFareProduct or In AmountOfPriceUnitProduct Ref for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_product = fare_products[0]
    fare_product_label = _get_fare_product_label_name(fare_product)
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""
    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:TypeOfFareProductRef"
    type_of_fare_product = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if type_of_fare_product:
        return ""

    sourceline_preassigned = fare_product.sourceline
    response_details = XMLViolationDetail(
        sourceline_preassigned,
        ErrorMessages.MESSAGE_OBSERVATION_TYPE_OF_FARE_MISSING.format(
            fare_product_label
        ),
    )
    response = response_details.__list__()
    return response


def check_product_type(_context: None, fare_products: _Element):
    """
    Check if mandatory element 'ProductType'is missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_product = fare_products[0]
    fare_product_label = _get_fare_product_label_name(fare_product)
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""
    xpath = "string(x:ProductType)"
    product_type = fare_product.xpath(xpath, namespaces=NAMESPACE)

    if not product_type:
        sourceline_fare_frame = fare_product.sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_frame,
            ErrorMessages.MESSAGE_OBSERVATION_PRODUCT_TYPE_MISSING.format(
                fare_product_label
            ),
        )
        response = response_details.__list__()
        return response

    if (
        fare_product_label == FARE_STRUCTURE_AMOUNT_OF_PRICE_UNIT_LABEL
        and not product_type in TYPE_OF_AMOUNT_OF_PRICE_UNIT_PRODUCT_TYPE
    ):
        sourceline_fare_frame = fare_product.sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_frame,
            ErrorMessages.MESSAGE_OBSERVATION_WRONG_PRODUCT_TYPE,
        )
        response = response_details.__list__()
        return response

    return ""
