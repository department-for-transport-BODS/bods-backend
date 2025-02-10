"""
Stop Point Information
"""

from common_layer.database.models import NaptanStopPoint
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.utils_location import osgrid_to_lonlat
from common_layer.xml.txc.models import (
    AnnotatedStopPointRef,
    LocationStructure,
    TXCStopPoint,
)
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from structlog.stdlib import get_logger

from ..helpers import StopsLookup

log = get_logger()


def convert_location_to_point(location: LocationStructure) -> Point:
    """
    Convert LocationStructure to Shapely Point in WGS84

    X = Longitude
    Y = Latitude
    """
    if location.Longitude and location.Latitude:
        return Point(float(location.Longitude), float(location.Latitude))
    if location.Easting and location.Northing:
        lon, lat = osgrid_to_lonlat(float(location.Easting), float(location.Northing))
        return Point(lon, lat)
    raise ValueError("Invalid location coordinates")


def create_custom_stop_point_data(stop: TXCStopPoint) -> NaptanStopPoint:
    """
    With Custom Stop Points
    it may be easier to work with if we create a NaptanStopPoint based on the TXC data
    TODO: Investigate how they use custom stop points
    """
    bus_stop_type = (
        stop.StopClassification.OnStreet.Bus.BusStopType
        if (stop.StopClassification.OnStreet and stop.StopClassification.OnStreet.Bus)
        else None
    )

    return NaptanStopPoint(
        atco_code=stop.AtcoCode,
        naptan_code=stop.NaptanCode,
        common_name=stop.Descriptor.CommonName,
        street=stop.Descriptor.Street,
        indicator=stop.Descriptor.Indicator,
        location=from_shape(convert_location_to_point(stop.Place.Location)),
        admin_area_id=int(stop.AdministrativeAreaRef),
        stop_areas=stop.StopAreas if stop.StopAreas else [],
        stop_type=stop.StopClassification.StopType,
        bus_stop_type=bus_stop_type,
        locality_id=stop.Place.NptgLocalityRef,
    )


def create_stop_point_location_mapping(
    stop_points: list[AnnotatedStopPointRef | TXCStopPoint],
    naptan_stops: list[TXCStopPoint],
) -> StopsLookup:
    """
    Create a mapping dict between AtcoCodes and it's location
    """
    stop_location_map: StopsLookup = {}

    for naptan in naptan_stops:
        stop_location_map[naptan.AtcoCode] = create_custom_stop_point_data(naptan)
    for stop in stop_points:
        if isinstance(stop, TXCStopPoint):
            stop_location_map[stop.AtcoCode] = create_custom_stop_point_data(stop)
    return stop_location_map


def get_naptan_stops_from_dynamo(
    stop_points: list[AnnotatedStopPointRef | TXCStopPoint],
    stop_point_client: NaptanStopPointDynamoDBClient,
) -> list[TXCStopPoint]:
    """
    Filter the TXC Stop Points for AnnotatedStopPointRef and query the DB for them
    TODO: Figure out how to handle when a referenced stop point ref is not in the DB
    """
    log.debug("Getting list of AnnotatedStopPointRef stops found in DB")
    stop_refs: list[str] = []
    for stop in stop_points:
        if isinstance(stop, AnnotatedStopPointRef):
            stop_refs.append(stop.StopPointRef)
    stops, missing_stops = stop_point_client.get_by_atco_codes(stop_refs)
    if missing_stops:
        log.error("AnnotatedStopPointRef not found in DB", missing_stops=missing_stops)
    log.info("Fetched naptan stops", count=len(stops), missing_stops=len(missing_stops))
    return stops
