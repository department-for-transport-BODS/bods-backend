"""
StopAreas List Parsing
"""

from typing import Final

from lxml import etree

from .xml_constants import NAPTAN_NS_PREFIX

STOP_AREAS_TAG: Final[str] = f"{NAPTAN_NS_PREFIX}StopAreas"
STOP_AREA_REF_TAG: Final[str] = f"{NAPTAN_NS_PREFIX}StopAreaRef"


def parse_stop_areas(stop_point: etree._Element) -> list[str]:
    """Extract stop areas from stop point using direct traversal."""
    result: list[str] = []

    for stop_areas in stop_point.iter(STOP_AREAS_TAG):
        for area_ref in stop_areas.iter(STOP_AREA_REF_TAG):
            if area_ref.get("Status") == "active" and area_ref.text:
                result.append(area_ref.text)
    return result
