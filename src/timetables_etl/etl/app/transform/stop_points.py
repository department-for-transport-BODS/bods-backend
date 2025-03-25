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
from geoalchemy2.shape import from_shape  # type: ignore
from shapely.geometry import Point
from structlog.stdlib import get_logger

from ..helpers import FlexibleZoneLookup, StopsLookup
from ..helpers.dataclasses import NonExistentNaptanStop

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

    stop_point = NaptanStopPoint(
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
    if stop.PrivateCode:
        stop_point.id = int(stop.PrivateCode)

    return stop_point


def create_non_existent_stop_point_data(
    stop_point_ref: AnnotatedStopPointRef,
) -> NonExistentNaptanStop:
    """
    Create a NonExistentNaptanStop

    In some cases Operators are using an AnnotatedStopPointRef
    instead of StopPoint for stops that don't exist in Naptan.
    """
    return NonExistentNaptanStop(
        atco_code=stop_point_ref.StopPointRef,
        common_name=stop_point_ref.CommonName,
    )


def get_flexible_zone_locations(stop_point: TXCStopPoint) -> list[LocationStructure]:
    """
    Get locations from FlexibleZone.Location for the given stop point
    """
    bus = (
        stop_point.StopClassification.OnStreet.Bus
        if stop_point.StopClassification.OnStreet
        else None
    )
    if bus and bus.FlexibleZone and bus.FlexibleZone.Location:
        return bus.FlexibleZone.Location
    return []


def create_stop_point_lookups(
    stop_points: list[AnnotatedStopPointRef | TXCStopPoint],
    naptan_stops: list[TXCStopPoint],
    missing_stop_atco_codes: list[str],
) -> tuple[StopsLookup, FlexibleZoneLookup]:
    """
    Create a mapping dict between AtcoCodes and it's location

    :param stop_points: Custom StopPoints.
    :param naptan_stops: AnnotatedStopPoints, retrieved from the Naptan DB.
    :param missing_stop_atco_codes: AnnotatedStopPoints that
    could not be found in the Naptan DB
    """
    stops_lookup: StopsLookup = {}
    flexible_zone_lookup: dict[str, list[LocationStructure]] = {}

    # Handle
    for naptan in naptan_stops:
        stops_lookup[naptan.AtcoCode] = create_custom_stop_point_data(naptan)
        flexible_zone_lookup[naptan.AtcoCode] = get_flexible_zone_locations(naptan)

    for stop in stop_points:
        if isinstance(stop, TXCStopPoint):
            stops_lookup[stop.AtcoCode] = create_custom_stop_point_data(stop)
            flexible_zone_lookup[stop.AtcoCode] = get_flexible_zone_locations(stop)

        # Handle AnnotatedStopPointRefs not found in Naptan DB
        if (
            isinstance(stop, AnnotatedStopPointRef)
            and stop.StopPointRef in missing_stop_atco_codes
        ):
            stops_lookup[stop.StopPointRef] = create_non_existent_stop_point_data(stop)
            flexible_zone_lookup[stop.StopPointRef] = []

    return stops_lookup, flexible_zone_lookup


def get_naptan_stops_from_dynamo(
    stop_points: list[AnnotatedStopPointRef | TXCStopPoint],
    stop_point_client: NaptanStopPointDynamoDBClient,
) -> tuple[list[TXCStopPoint], list[str]]:
    """
    Filter the TXC Stop Points for AnnotatedStopPointRef and query the DB for them
    TODO: Figure out how to handle when a referenced stop point ref is not in the DB

    Returns: (TXCStopPoints, missing_stop_atco_codes)
    """
    log.debug("Getting list of AnnotatedStopPointRef stops found in DB")
    stop_refs: list[str] = []
    for stop in stop_points:
        if isinstance(stop, AnnotatedStopPointRef):
            stop_refs.append(stop.StopPointRef)
    stops, missing_stops = stop_point_client.get_by_atco_codes(stop_refs)
    if missing_stops:
        log.warning(
            "AnnotatedStopPointRef(s) not found in DB",
            missing_stops=missing_stops,
        )

    log.info("Fetched naptan stops", count=len(stops), missing_stops=len(missing_stops))
    return stops, missing_stops
