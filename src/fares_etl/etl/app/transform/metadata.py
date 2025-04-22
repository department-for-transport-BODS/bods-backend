"""
Create fares metadata
"""

from common_layer.database.models import FaresMetadata
from common_layer.dynamodb.client import NaptanStopPointDynamoDBClient
from common_layer.xml.netex.helpers import (
    earliest_tariff_from_date,
    get_fare_products,
    get_scheduled_stop_point_refs,
    get_tariffs_from_fare_frames,
    latest_tariff_to_date,
    number_of_distinct_user_profiles,
    number_of_fare_zones,
    number_of_lines,
    number_of_pass_fare_products,
    number_of_sales_offer_packages,
    number_of_trip_fare_products,
    sort_frames,
)
from common_layer.xml.netex.models import PublicationDeliveryStructure
from structlog.stdlib import get_logger

log = get_logger()


def create_metadata(netex: PublicationDeliveryStructure) -> FaresMetadata:
    """
    Create FaresMetadata
    """
    sorted_frames = sort_frames(netex.dataObjects)

    tariffs = get_tariffs_from_fare_frames(sorted_frames.fare_frames)
    fare_products = get_fare_products(sorted_frames.fare_frames)
    fares_metadata = FaresMetadata(
        num_of_lines=number_of_lines(sorted_frames.service_frames),
        num_of_fare_zones=number_of_fare_zones(sorted_frames.fare_frames),
        num_of_sales_offer_packages=number_of_sales_offer_packages(
            sorted_frames.fare_frames
        ),
        num_of_fare_products=len(fare_products),
        num_of_user_profiles=number_of_distinct_user_profiles(tariffs),
        num_of_pass_products=number_of_pass_fare_products(fare_products),
        num_of_trip_products=number_of_trip_fare_products(fare_products),
        valid_from=earliest_tariff_from_date(tariffs),
        valid_to=latest_tariff_to_date(tariffs),
    )
    log.info("Created FaresMetadata", **fares_metadata.as_dict())
    return fares_metadata


def get_stop_ids(
    netex: PublicationDeliveryStructure,
    dynamodb_naptan_stop_point_client: NaptanStopPointDynamoDBClient,
) -> list[int]:
    """
    Get list of stop PrivateCodes from NeTEx
    """
    sorted_frames = sort_frames(netex.dataObjects)
    stop_point_refs = get_scheduled_stop_point_refs(sorted_frames.fare_frames)

    atco_ids = {stop.atco_code for stop in stop_point_refs if stop.atco_code}
    naptan_ids = {stop.naptan_code for stop in stop_point_refs if stop.naptan_code}

    stops_from_atco_ids = dynamodb_naptan_stop_point_client.get_by_atco_codes(
        sorted(atco_ids)
    )[0]

    stops_from_naptan_ids = dynamodb_naptan_stop_point_client.get_by_naptan_codes(
        sorted(naptan_ids)
    )[0]

    stops = stops_from_atco_ids + stops_from_naptan_ids
    stop_ids = {
        int(stop.PrivateCode)
        for stop in stops
        if stop.PrivateCode is not None and stop.PrivateCode.isdigit()
    }
    log.info("Generated List of Stop Private Codes in Netex", stop_ids=stop_ids)
    return list(stop_ids)
