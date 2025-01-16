"""
StopPoint Location Tag Parsing
"""

from typing import Final

from common_layer.utils_location import osgrid_to_latlon
from lxml import etree

from .xml_constants import NAPTAN_NS_PREFIX

LOCATION_TAG: Final[str] = f"{NAPTAN_NS_PREFIX}Translation"

LOCATION_TAGS: Final[dict[str, str]] = {
    f"{NAPTAN_NS_PREFIX}Longitude": "Longitude",
    f"{NAPTAN_NS_PREFIX}Latitude": "Latitude",
    f"{NAPTAN_NS_PREFIX}Easting": "Easting",
    f"{NAPTAN_NS_PREFIX}Northing": "Northing",
}


def augment_location_data(
    location_data: dict[str, str | None]
) -> dict[str, str | None]:
    """
    Augment location data by converting Easting/Northing to Longitude/Latitude
    if Longitude/Latitude are not present.

    """
    if location_data.get("Longitude") and location_data.get("Latitude"):
        return location_data
    if not (location_data["Easting"] and location_data["Northing"]):
        return location_data

    try:
        easting = float(location_data["Easting"])
        northing = float(location_data["Northing"])
    except (TypeError, ValueError):
        return location_data

    try:
        longitude, latitude = osgrid_to_latlon(easting, northing)
        location_data.update(
            {"Longitude": str(round(longitude, 7)), "Latitude": str(round(latitude, 7))}
        )
    # We need to Skip StopPoints with errors and process all stops
    except Exception:  # pylint: disable=broad-exception-caught
        return location_data

    return location_data


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

        result = augment_location_data(result)
        if result["Longitude"] and result["Latitude"]:
            return result
        return None

    return None
