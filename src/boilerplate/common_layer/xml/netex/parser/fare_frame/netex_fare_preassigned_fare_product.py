"""
Parsing a Preassigned Fare Product
"""

from common_layer.xml.netex.models.netex_utility import VersionedRef
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models.fare_frame.netex_fare_preassigned import (
    AccessRightInProduct,
    ConditionSummary,
    PreassignedFareProduct,
    ValidableElement,
)
from ..netex_utility import (
    get_netex_bool,
    get_netex_text,
    parse_multilingual_string,
    parse_versioned_ref,
)
from .netex_fare_validable_element import parse_validable_element

log = get_logger()


def parse_condition_summary(elem: _Element) -> ConditionSummary:
    """Parse ConditionSummary element"""
    fare_structure_type = get_netex_text(elem, "FareStructureType")
    tariff_basis = get_netex_text(elem, "TariffBasis")
    is_personal = get_netex_bool(elem, "IsPersonal")

    if fare_structure_type is None or tariff_basis is None or is_personal is None:
        raise ValueError("Missing required fields in ConditionSummary")

    return ConditionSummary(
        FareStructureType=fare_structure_type,
        TariffBasis=tariff_basis,
        IsPersonal=is_personal,
    )


def parse_access_right_in_product(elem: _Element) -> AccessRightInProduct:
    """Parse AccessRightInProduct element"""
    access_right_id = elem.get("id")
    version = elem.get("version")
    order = elem.get("order")

    if not access_right_id or not version or not order:
        raise ValueError("Missing required attributes in AccessRightInProduct")

    validable_element_ref = parse_versioned_ref(elem, "ValidableElementRef")
    if validable_element_ref is None:
        raise ValueError("Missing required ValidableElementRef in AccessRightInProduct")

    return AccessRightInProduct(
        id=access_right_id,
        version=version,
        order=order,
        ValidableElementRef=validable_element_ref,
    )


def parse_preassigned_product_attributes(elem: _Element) -> tuple[str, str]:
    """Parse required id and version attributes"""
    product_id = elem.get("id")
    version = elem.get("version")

    if not product_id or not version:
        raise ValueError("Missing required id or version in PreassignedFareProduct")

    return product_id, version


def parse_preassigned_product_refs(
    elem: _Element,
) -> tuple[VersionedRef, VersionedRef, VersionedRef]:
    """Parse required references"""
    charging_moment_ref = parse_versioned_ref(elem, "ChargingMomentRef")
    if charging_moment_ref is None:
        raise ValueError("Missing required ChargingMomentRef in PreassignedFareProduct")

    type_of_fare_product_ref = parse_versioned_ref(elem, "TypeOfFareProductRef")
    if type_of_fare_product_ref is None:
        raise ValueError(
            "Missing required TypeOfFareProductRef in PreassignedFareProduct"
        )

    operator_ref = parse_versioned_ref(elem, "OperatorRef")
    if operator_ref is None:
        raise ValueError("Missing required OperatorRef in PreassignedFareProduct")

    return charging_moment_ref, type_of_fare_product_ref, operator_ref


def parse_validable_elements_list(elem: _Element) -> list[ValidableElement]:
    """Parse validableElements list"""
    elements: list[ValidableElement] = []
    for validable_elem in elem:
        if get_tag_name(validable_elem) == "ValidableElement":
            validable_element = parse_validable_element(validable_elem)
            if validable_element:
                elements.append(validable_element)
        else:
            log.warning(
                "Unknown validableElements tag", tag=get_tag_name(validable_elem)
            )
    return elements


def parse_access_rights_list(elem: _Element) -> list[AccessRightInProduct]:
    """Parse accessRightsInProduct list"""
    rights: list[AccessRightInProduct] = []
    for access_right in elem:
        if get_tag_name(access_right) == "AccessRightInProduct":
            rights.append(parse_access_right_in_product(access_right))
        else:
            log.warning(
                "Unknown accessRightsInProduct tag", tag=get_tag_name(access_right)
            )
    return rights


def parse_preassigned_fare_product(elem: _Element) -> PreassignedFareProduct:
    """Parse PreassignedFareProduct element"""
    product_id, version = parse_preassigned_product_attributes(elem)

    name = parse_multilingual_string(elem, "Name")
    if name is None:
        name = get_netex_text(elem, "Name")
        if name is None:
            raise ValueError("Missing required Name in PreassignedFareProduct")

    charging_moment_ref, type_of_fare_product_ref, operator_ref = (
        parse_preassigned_product_refs(elem)
    )

    charging_moment_type = get_netex_text(elem, "ChargingMomentType")
    if charging_moment_type is None:
        raise ValueError(
            "Missing required ChargingMomentType in PreassignedFareProduct"
        )

    product_type = get_netex_text(elem, "ProductType")
    if product_type is None:
        raise ValueError("Missing required ProductType in PreassignedFareProduct")

    validable_elements: list[ValidableElement] = []
    access_rights: list[AccessRightInProduct] = []
    condition_summary = None

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "ConditionSummary":
                condition_summary = parse_condition_summary(child)
            case "validableElements":
                validable_elements = parse_validable_elements_list(child)
            case "accessRightsInProduct":
                access_rights = parse_access_rights_list(child)
            case (
                "Name"
                | "ChargingMomentRef"
                | "ChargingMomentType"
                | "TypeOfFareProductRef"
                | "OperatorRef"
                | "ProductType"
            ):
                pass
            case _:
                log.warning("Unknown PreassignedFareProduct tag", tag=tag)
        child.clear()

    if condition_summary is None:
        raise ValueError("Missing required ConditionSummary in PreassignedFareProduct")

    return PreassignedFareProduct(
        id=product_id,
        version=version,
        Name=name,
        ChargingMomentRef=charging_moment_ref,
        ChargingMomentType=charging_moment_type,
        TypeOfFareProductRef=type_of_fare_product_ref,
        OperatorRef=operator_ref,
        ConditionSummary=condition_summary,
        validableElements=validable_elements,
        accessRightsInProduct=access_rights,
        ProductType=product_type,
    )


def parse_preassigned_fare_products(elem: _Element) -> list[PreassignedFareProduct]:
    """Parse fareProducts list element"""
    fare_products: list[PreassignedFareProduct] = []
    for product in elem:
        if get_tag_name(product) == "PreassignedFareProduct":
            fare_product = parse_preassigned_fare_product(product)
            if fare_product is not None:
                fare_products.append(fare_product)
        else:
            log.warning("Unknown fareProducts tag", tag=get_tag_name(product))
    return fare_products
