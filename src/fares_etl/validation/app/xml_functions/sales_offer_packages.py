from lxml.etree import _Element  # type: ignore

from ..constants import (
    NAMESPACE,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    ErrorMessages,
)
from ..types import XMLViolationDetail
from .helpers import extract_attribute


def check_dist_assignments(_context: None, sales_offer_packages: _Element):
    """
    Check if mandatory salesOfferPackage.distributionAssignments elements
    missing for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    sales_offer_package = sales_offer_packages[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = sales_offer_package.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:distributionAssignments"
    distribution_assignments = sales_offer_package.xpath(xpath, namespaces=NAMESPACE)

    if not distribution_assignments:
        sourceline_sales_offer_package = sales_offer_package.sourceline
        response_details = XMLViolationDetail(
            sourceline_sales_offer_package,
            ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENTS_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "x:DistributionAssignment"
    distribution_assignment = distribution_assignments[0].xpath(
        xpath, namespaces=NAMESPACE
    )

    if not distribution_assignment:
        sourceline_distribution_assignments = distribution_assignments[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_distribution_assignments,
            ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENT_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "string(x:DistributionChannelType)"
    distribution_type = distribution_assignment[0].xpath(xpath, namespaces=NAMESPACE)

    if not distribution_type:
        sourceline_distribution_assignment = distribution_assignment[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_distribution_assignment,
            ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_DIST_CHANNEL_TYPE_MISSING,
        )
        response = response_details.__list__()
        return response

    return ""


def check_fare_product_ref(_context: None, sales_offer_package_elements: _Element):
    """
    Check if mandatory element 'PreassignedFareProductRef' is missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    sales_offer_package_element = sales_offer_package_elements[0]
    xpath = "../../../../x:TypeOfFrameRef"
    type_of_frame_refs = sales_offer_package_element.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:PreassignedFareProductRef"
    fare_product_ref = sales_offer_package_element.xpath(xpath, namespaces=NAMESPACE)

    if fare_product_ref:
        return ""

    xpath = "x:AmountOfPriceUnitProductRef"
    fare_product_ref = sales_offer_package_element.xpath(xpath, namespaces=NAMESPACE)

    if fare_product_ref:
        return ""

    sourceline_sales_offer_package_element = sales_offer_package_element.sourceline
    response_details = XMLViolationDetail(
        sourceline_sales_offer_package_element,
        ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_FARE_PROD_REF_MISSING,
    )
    response = response_details.__list__()
    return response


def check_payment_methods(_context: None, distribution_assignments: _Element):
    """
    Check if mandatory element 'PaymentMethods' is missing for DistributionAssignment in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    distribution_assignment = distribution_assignments[0]
    xpath = "../../../../x:TypeOfFrameRef"
    type_of_frame_refs = distribution_assignment.xpath(xpath, namespaces=NAMESPACE)
    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "string(x:PaymentMethods)"
    payment_method = distribution_assignment.xpath(xpath, namespaces=NAMESPACE)
    if not payment_method:
        sourceline_distribution_assignment = distribution_assignment.sourceline
        response_details = XMLViolationDetail(
            sourceline_distribution_assignment,
            ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_PAYMENT_METHODS_MISSING,
        )
        response = response_details.__list__()
        return response

    return ""


def check_sale_offer_package_elements(_context: None, sales_offer_packages: _Element):
    """
    Check if mandatory element 'salesOfferPackageElements' or it's children missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    sales_offer_package = sales_offer_packages[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = sales_offer_package.xpath(xpath, namespaces=NAMESPACE)

    if not type_of_frame_refs:
        return ""

    try:
        type_of_frame_ref_ref = extract_attribute(type_of_frame_refs, "ref")
    except KeyError:
        return ""

    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING not in type_of_frame_ref_ref:
        return ""

    xpath = "x:salesOfferPackageElements"
    sales_offer_elements = sales_offer_package.xpath(xpath, namespaces=NAMESPACE)

    if not sales_offer_elements:
        sourceline_sales_offer_package = sales_offer_package.sourceline
        response_details = XMLViolationDetail(
            sourceline_sales_offer_package,
            ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_ELEMENTS_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "x:SalesOfferPackageElement"
    sales_offer_element = sales_offer_elements[0].xpath(xpath, namespaces=NAMESPACE)

    if not sales_offer_element:
        sourceline_sales_package_elements = sales_offer_elements[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_sales_package_elements,
            ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_ELEMENT_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "x:TypeOfTravelDocumentRef"
    type_of_travel_document_ref = sales_offer_element[0].xpath(
        xpath, namespaces=NAMESPACE
    )

    if not type_of_travel_document_ref:
        sourceline_sales_offer_element = sales_offer_element[0].sourceline
        response_details = XMLViolationDetail(
            sourceline_sales_offer_element,
            ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_TRAVEL_DOC_MISSING,
        )
        response = response_details.__list__()
        return response

    return ""


def check_sales_offer_package(_context: None, fare_frames: _Element):
    """
    Check if mandatory salesOfferPackages elements missing
    for FareFrame - UK_PI_FARE_PRODUCT.
    FareFrame UK_PI_FARE_PRODUCT is mandatory.
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

    xpath = "x:salesOfferPackages"
    sales_offer_packages = fare_frame.xpath(xpath, namespaces=NAMESPACE)

    if not sales_offer_packages:
        sourceline_fare_frame = fare_frame.sourceline
        response_details = XMLViolationDetail(
            sourceline_fare_frame,
            ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_PACKAGES_MISSING,
        )
        response = response_details.__list__()
        return response

    xpath = "x:SalesOfferPackage"
    sales_offer_package = sales_offer_packages[0].xpath(xpath, namespaces=NAMESPACE)

    if sales_offer_package:
        return ""

    sourceline_sales_offer_packages = sales_offer_packages[0].sourceline
    response_details = XMLViolationDetail(
        sourceline_sales_offer_packages,
        ErrorMessages.MESSAGE_OBSERVATION_SALES_OFFER_PACKAGE_MISSING,
    )
    response = response_details.__list__()
    return response
