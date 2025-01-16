"""
Parse Description
"""

from typing import Final

from lxml import etree

from .xml_constants import NAPTAN_NS_PREFIX

DESCRIPTOR_TAG: Final[str] = f"{NAPTAN_NS_PREFIX}Descriptor"
DESCRIPTOR_TAGS: Final[dict[str, str]] = {
    f"{NAPTAN_NS_PREFIX}CommonName": "CommonName",
    f"{NAPTAN_NS_PREFIX}ShortCommonName": "ShortCommonName",
    f"{NAPTAN_NS_PREFIX}Street": "Street",
    f"{NAPTAN_NS_PREFIX}Landmark": "Landmark",
    f"{NAPTAN_NS_PREFIX}Indicator": "Indicator",
}


def parse_descriptor(stop_point: etree._Element) -> dict[str, str | None]:
    """Extract descriptor data from stop point with minimal traversal."""

    for descriptor in stop_point:
        if descriptor.tag == DESCRIPTOR_TAG:
            result: dict[str, str | None] = {
                "CommonName": None,
                "ShortCommonName": None,
                "Street": None,
                "Landmark": None,
                "Indicator": None,
            }

            for child in descriptor:
                if child.tag in DESCRIPTOR_TAGS:
                    result[DESCRIPTOR_TAGS[child.tag]] = child.text or None

            return result

    return {
        "CommonName": None,
        "ShortCommonName": None,
        "Street": None,
        "Landmark": None,
        "Indicator": None,
    }
