"""
Validable Element
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import VersionedRef
from ...models.fare_frame.netex_fare_preassigned import ValidableElement
from ..netex_utility import get_netex_element, parse_multilingual_string

log = get_logger()


def parse_validable_element(elem: _Element) -> ValidableElement | None:
    """
    Parse a single ValidableElement.
    """
    element_id = elem.get("id")
    element_version = elem.get("version")
    name = parse_multilingual_string(elem, "Name")

    if not element_id or not element_version or not name:
        log.warning(
            "ValidableElement missing required fields",
            id=element_id,
            version=element_version,
            name=name,
        )
        return None

    fare_elements: list[VersionedRef] = []
    fare_elements_container = get_netex_element(elem, "fareStructureElements")

    if fare_elements_container is not None:
        for child in fare_elements_container:
            tag_name = get_tag_name(child)
            if tag_name == "FareStructureElementRef":
                ref = child.get("ref")
                version = child.get("version")
                if ref and version:
                    fare_elements.append(VersionedRef(ref=ref, version=version))

    return ValidableElement(
        id=element_id,
        version=element_version,
        Name=name,
        fareStructureElements=fare_elements,
    )
