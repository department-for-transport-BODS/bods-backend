"""
Parse StopClassification
Optimised for Speed
"""

from typing import Final

from lxml import etree

from .xml_constants import NAPTAN_NS_PREFIX

CLASSIFICATION_TAGS: Final[dict[str, str]] = {
    f"{NAPTAN_NS_PREFIX}StopType": "StopType",
    f"{NAPTAN_NS_PREFIX}BusStopType": "BusStopType",
}

CLASSIFICATION_TAG: Final[str] = f"{NAPTAN_NS_PREFIX}StopClassification"
ONSTREET_TAG: Final[str] = f"{NAPTAN_NS_PREFIX}OnStreet"
BUS_TAG: Final[str] = f"{NAPTAN_NS_PREFIX}Bus"
BUS_STOP_TYPE_TAG: Final[str] = f"{NAPTAN_NS_PREFIX}BusStopType"


def extract_bus_stop_type(onstreet_element: etree._Element) -> str | None:
    """Extract bus stop type from OnStreet element."""
    for bus_container in onstreet_element:
        if bus_container.tag != BUS_TAG:
            continue

        for bus_element in bus_container:
            if bus_element.tag == BUS_STOP_TYPE_TAG:
                return bus_element.text or None
    return None


def parse_stop_classification(stop_point: etree._Element) -> dict[str, str | None]:
    """Extract stop classification data from stop point with minimal traversal."""
    result: dict[str, str | None] = {"StopType": None, "BusStopType": None}

    for child in stop_point:
        if child.tag != CLASSIFICATION_TAG:
            continue

        for element in child:
            if element.tag in CLASSIFICATION_TAGS:
                result[CLASSIFICATION_TAGS[element.tag]] = element.text or None
            elif element.tag == ONSTREET_TAG:
                result["BusStopType"] = extract_bus_stop_type(element)
        return result

    return result
