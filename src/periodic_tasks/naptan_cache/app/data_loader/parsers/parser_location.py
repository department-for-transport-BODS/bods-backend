"""
StopPoint Location Tag Parsing
"""

from typing import Final

from lxml import etree

from .xml_constants import NAPTAN_NS_PREFIX

LOCATION_TAG: Final[str] = f"{NAPTAN_NS_PREFIX}Translation"

LOCATION_TAGS: Final[dict[str, str]] = {
    f"{NAPTAN_NS_PREFIX}Longitude": "Longitude",
    f"{NAPTAN_NS_PREFIX}Latitude": "Latitude",
    f"{NAPTAN_NS_PREFIX}Easting": "Easting",
    f"{NAPTAN_NS_PREFIX}Northing": "Northing",
}


def parse_location(stop_point: etree._Element) -> dict[str, str | None] | None:
    """Extract location data from stop point with minimal traversal."""

    for location in stop_point.iter(LOCATION_TAG):
        result: dict[str, str | None] = {
            "Longitude": None,
            "Latitude": None,
            "Easting": None,
            "Northing": None,
        }

        for child in location:
            if child.tag in LOCATION_TAGS:
                result[LOCATION_TAGS[child.tag]] = child.text or None

        if result["Easting"] and result["Northing"]:
            return result

        return None

    return None
