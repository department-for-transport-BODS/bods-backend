"""
Location Helpers
EPSG:27700 = OSGB36 (Easting / Northing)
EPSG:4326 = WGS84 (Logitude / Latitude)
Instantiate Transformer once
"""

from pyproj import Transformer

osgrid_to_lonlat_transformer = Transformer.from_crs(
    "EPSG:27700",
    "EPSG:4326",
    always_xy=True,
)
lonlat_to_osgrid_transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:27700",
    always_xy=True,
)


def osgrid_to_lonlat(easting: float, northing: float) -> tuple[float, float]:
    """
    Convert OSGB36 coordinates to WGS84 lat/lon

    Returns a Tuple of Floats with Longitude,Latitude in that order
    """
    lon, lat = osgrid_to_lonlat_transformer.transform(easting, northing)
    return lon, lat


def lonlat_to_osgrid(longitude: float, latitude: float) -> tuple[int, int]:
    """
    Convert WGS84 long/lat coordinates to OSGB36 Easting/Northing

    Returns a Tuple of Integers with Easting,Northing in that order
    """
    easting, northing = lonlat_to_osgrid_transformer.transform(longitude, latitude)
    return int(round(easting)), int(round(northing))
