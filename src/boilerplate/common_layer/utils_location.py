"""
Location Helpers
EPSG:27700 = OSGB36 (Easting / Northing)
EPSG:4326 = WGS84 (Logitude / Latitude)
Instantiate Transformer once
"""

from pyproj import Transformer

osgrid_to_latlon_transformer = Transformer.from_crs(
    "EPSG:27700",
    "EPSG:4326",
    always_xy=True,
)


def osgrid_to_latlon(easting: float, northing: float) -> tuple[float, float]:
    """
    Convert OSGB36 coordinates to WGS84 lat/lon
    """
    lon, lat = osgrid_to_latlon_transformer.transform(easting, northing)
    return lon, lat
