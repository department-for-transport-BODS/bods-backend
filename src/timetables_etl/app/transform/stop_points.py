"""
Stop Point Information
"""

from typing import cast

from geoalchemy2.shape import to_shape
from pyproj import Transformer
from shapely.geometry import Point
from structlog.stdlib import get_logger

from ..database import BodsDB
from ..database.models.model_naptan import NaptanStopPoint
from ..database.repos.repo_naptan import NaptanStopPointRepo
from ..txc.models.txc_stoppoint import (
    AnnotatedStopPointRef,
    LocationStructure,
    TXCStopPoint,
)

log = get_logger()

"""
EPSG:27700 = OSGB36 (Easting / Northing)
EPSG:4326 = WGS84 (Logitude / Latitude)
Instantiate Transformer once
"""
osgrid_to_latlon_transformer = Transformer.from_crs(
    "EPSG:27700", "EPSG:4326", always_xy=True
)


def osgrid_to_latlon(easting: float, northing: float) -> tuple[float, float]:
    """
    Convert OSGB36 coordinates to WGS84 lat/lon
    """
    lon, lat = osgrid_to_latlon_transformer.transform(easting, northing)
    return lon, lat


def convert_location_to_point(location: LocationStructure) -> Point:
    """
    Convert LocationStructure to Shapely Point in WGS84

    X = Longitude
    Y = Latitude
    """
    if location.Longitude and location.Latitude:
        return Point(float(location.Longitude), float(location.Latitude))
    if location.Easting and location.Northing:
        lon, lat = osgrid_to_latlon(float(location.Easting), float(location.Northing))
        return Point(lon, lat)
    raise ValueError("Invalid location coordinates")


def create_stop_point_location_mapping(
    stop_points: list[AnnotatedStopPointRef | TXCStopPoint],
    naptan_stops: list[NaptanStopPoint],
) -> dict[str, Point]:
    """
    Create a mapping dict between AtcoCodes and it's location
    """
    stop_location_map: dict[str, Point] = {}

    for naptan in naptan_stops:
        point = cast(Point, to_shape(naptan.location))
        stop_location_map[naptan.atco_code] = point
    for stop in stop_points:
        if isinstance(stop, TXCStopPoint):
            stop_location_map[stop.AtcoCode] = convert_location_to_point(
                stop.Place.Location
            )
    return stop_location_map


def get_naptan_stops_from_db(
    stop_points: list[AnnotatedStopPointRef | TXCStopPoint], db: BodsDB
) -> list[NaptanStopPoint]:
    """
    Filter the TXC Stop Points for AnnotatedStopPointRef and query the DB
    """
    stop_refs: list[str] = []
    for stop in stop_points:
        if isinstance(stop, AnnotatedStopPointRef):
            stop_refs.append(stop.StopPointRef)
    stops, missing_stops = NaptanStopPointRepo(db).get_by_atco_codes(stop_refs)
    if missing_stops:
        # TODO: Figure out how to handle this scenario
        log.error("AnnotatedStopPointRef not found in DB", missing_stops=missing_stops)
    return stops
