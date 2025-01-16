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


def convert_osgrid_to_lonlat(
    easting: str | None, northing: str | None
) -> tuple[str, str] | None:
    """
    Convert OS Grid coordinates to longitude/latitude if possible.
    Returns (longitude, latitude) as strings with 5 decimal places,
    or
    None if conversion fails.
    """
    if easting is None or northing is None:
        return None

    try:
        east = float(easting)
        north = float(northing)
        lon, lat = osgrid_to_lonlat(east, north)
        return f"{lon:.5f}", f"{lat:.5f}"
    except (ValueError, TypeError):
        return None


def convert_lonlat_to_osgrid(
    longitude: str | None, latitude: str | None
) -> tuple[str, str] | None:
    """
    Convert longitude/latitude to OS Grid coordinates if possible.
    Returns (easting, northing) as strings, or None if conversion fails.
    """
    if longitude is None or latitude is None:
        return None

    try:
        lon = float(longitude)
        lat = float(latitude)
        east, north = lonlat_to_osgrid(lon, lat)
        return str(east), str(north)
    except (ValueError, TypeError):
        return None


def augment_location_data(
    location_data: dict[str, str | None]
) -> dict[str, str | None]:
    """
    Augment location data by converting between coordinate systems.
    """
    # Exit early if all locations are present
    if all(
        location_data.get(key)
        for key in ["Longitude", "Latitude", "Easting", "Northing"]
    ):
        return location_data

    # Try converting from OS Grid to Lon/Lat
    if not all(location_data.get(key) for key in ["Longitude", "Latitude"]):
        result = convert_osgrid_to_lonlat(
            location_data.get("Easting"), location_data.get("Northing")
        )
        if result:
            longitude, latitude = result
            location_data["Longitude"] = longitude
            location_data["Latitude"] = latitude

    # Try converting from Lon/Lat to OS Grid
    if not all(location_data.get(key) for key in ["Easting", "Northing"]):
        result = convert_lonlat_to_osgrid(
            location_data.get("Longitude"), location_data.get("Latitude")
        )
        if result:
            easting, northing = result
            location_data["Easting"] = easting
            location_data["Northing"] = northing

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
