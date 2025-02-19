"""
PreassignedFareProduct
"""

from lxml.etree import _Element
from structlog.stdlib import get_logger

from ...models import AccessRightInProduct, VersionedRef
from ..netex_utility import get_netex_element

log = get_logger()


def parse_access_right_in_product(elem: _Element) -> AccessRightInProduct | None:
    """
    Parse a single AccessRightInProduct element.
    """
    element_id = elem.get("id")
    element_version = elem.get("version")
    element_order = elem.get("order")

    if not element_id or not element_version or not element_order:
        log.warning(
            "AccessRightInProduct missing required fields",
            id=element_id,
            version=element_version,
            order=element_order,
        )
        return None

    validable_element_ref = get_netex_element(elem, "ValidableElementRef")
    if validable_element_ref is None:
        log.warning("AccessRightInProduct missing ValidableElementRef")
        return None

    ref = validable_element_ref.get("ref")
    version = validable_element_ref.get("version")
    if not ref or not version:
        log.warning("ValidableElementRef missing required fields")
        return None

    return AccessRightInProduct(
        id=element_id,
        version=element_version,
        order=element_order,
        ValidableElementRef=VersionedRef(ref=ref, version=version),
    )
