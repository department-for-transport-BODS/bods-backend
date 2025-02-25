"""
Create fares metadata
"""

from common_layer.database.models.model_fares import FaresMetadata
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.xml.netex.helpers.helpers_counts import (
    number_of_distinct_user_profiles,
    number_of_fare_zones,
    number_of_lines,
    number_of_pass_fare_products,
    number_of_sales_offer_packages,
    number_of_trip_fare_products,
    sort_frames,
)
from common_layer.xml.netex.helpers.helpers_fare_frame_fare_products import (
    get_fare_products,
)
from common_layer.xml.netex.helpers.helpers_fare_frame_tariff import (
    earliest_tariff_from_date,
    get_tariffs_from_fare_frames,
    latest_tariff_to_date,
)
from common_layer.xml.netex.helpers.helpers_fare_frame_zones import (
    get_scheduled_stop_point_refs,
)
from common_layer.xml.netex.models.netex_publication_delivery import (
    PublicationDeliveryStructure,
)


def create_metadata(
    netex: PublicationDeliveryStructure, metadata_dataset_id: int
) -> FaresMetadata:
    """
    Create FaresMetadata
    """
    sorted_frames = sort_frames(netex.dataObjects)

    tariffs = get_tariffs_from_fare_frames(sorted_frames.fare_frames)
    fare_products = get_fare_products(sorted_frames.fare_frames)

    return FaresMetadata(
        datasetmetadata_ptr_id=metadata_dataset_id,
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


def get_stop_ids(
    netex: PublicationDeliveryStructure, naptan_stop_point_repo: NaptanStopPointRepo
) -> list[int]:
    """
    Create FaresMetadataStops
    """
    sorted_frames = sort_frames(netex.dataObjects)
    stop_point_refs = get_scheduled_stop_point_refs(sorted_frames.fare_frames)

    naptan_ids = set()
    atco_ids = set()

    for stop in stop_point_refs:
        if stop.atco_code:
            atco_ids.add(stop.atco_code)

        if stop.naptan_code:
            naptan_ids.add(stop.naptan_code)

    stops_from_atco_ids = naptan_stop_point_repo.get_by_atco_codes(
        sorted(list(atco_ids))
    )[0]
    stops_from_naptan_ids = naptan_stop_point_repo.get_by_naptan_codes(
        sorted(list(naptan_ids))
    )[0]

    stops = stops_from_atco_ids + stops_from_naptan_ids
    stop_ids = [stop.id for stop in stops]

    return list(set(stop_ids))
