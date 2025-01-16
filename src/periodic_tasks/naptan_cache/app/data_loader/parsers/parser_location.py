"""
StopPoint Location Tag Parsing
"""

from typing import Final

from common_layer.utils_location import lonlat_to_osgrid, osgrid_to_lonlat
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
    Augment location data by converting between coordinate systems.
    """
    # Exit Early if all locations are there
    if all(
        location_data.get(key)
        for key in ["Longitude", "Latitude", "Easting", "Northing"]
    ):
        return location_data

    # Define coordinate conversion strategies
    conversions = [
        {
            "missing_keys": ["Longitude", "Latitude"],
            "existing_keys": ["Easting", "Northing"],
            "converter": osgrid_to_lonlat,
            "format_fn": lambda x: f"{x:.15f}",
            "result_keys": ["Longitude", "Latitude"],
        },
        {
            "missing_keys": ["Easting", "Northing"],
            "existing_keys": ["Longitude", "Latitude"],
            "converter": lonlat_to_osgrid,
            "format_fn": str,
            "result_keys": ["Easting", "Northing"],
        },
    ]

    for conversion in conversions:
        # Skip if the coordinates we want are already present
        if all(location_data.get(key) for key in conversion["missing_keys"]):
            continue

        # Check if we have the existing coordinates to convert from
        if not all(location_data.get(key) for key in conversion["existing_keys"]):
            continue

        # Convert existing coordinates to floats, handling potential None
        coords = []
        for key in conversion["existing_keys"]:
            value = location_data.get(key)
            if value is None:
                break
            coords.append(float(value))

        # If we couldn't convert all coordinates, skip this conversion
        if len(coords) != len(conversion["existing_keys"]):
            continue

        # Perform coordinate conversion
        converted_coords = conversion["converter"](*coords)

        # Update location data with converted coordinates
        location_data.update(
            dict(
                zip(
                    conversion["result_keys"],
                    [conversion["format_fn"](coord) for coord in converted_coords],
                )
            )
        )

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
