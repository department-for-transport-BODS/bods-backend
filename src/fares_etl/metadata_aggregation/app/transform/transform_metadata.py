"""
Transform fares metadata items
"""

from dataclasses import asdict
from typing import Any

from boto3.dynamodb.types import TypeDeserializer
from common_layer.database.models import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
    FaresMetadataStop,
)
from structlog.stdlib import get_logger

log = get_logger()


def get_min_schema_version(schema_versions: list[str]) -> str:
    """
    Returns the lowest schema version in list
    """
    if len(schema_versions) == 0:
        return "1.1"

    return min(schema_versions)


def sum_metadata_fields(metadata_items: list[FaresMetadata]) -> FaresMetadata:
    """
    Sums the FaresMetadata and calculates the overall date range
    """
    aggregated_metadata = FaresMetadata(
        num_of_fare_products=0,
        num_of_fare_zones=0,
        num_of_lines=0,
        num_of_pass_products=0,
        num_of_sales_offer_packages=0,
        num_of_trip_products=0,
        num_of_user_profiles=0,
        valid_from=None,
        valid_to=None,
    )

    sum_fields = [
        "num_of_fare_products",
        "num_of_fare_zones",
        "num_of_lines",
        "num_of_sales_offer_packages",
    ]

    for item in metadata_items:
        for field in sum_fields:
            setattr(
                aggregated_metadata,
                field,
                getattr(item, field, 0) + getattr(aggregated_metadata, field, 0),
            )

        if item.valid_from and (
            not aggregated_metadata.valid_from
            or item.valid_from < aggregated_metadata.valid_from
        ):
            aggregated_metadata.valid_from = item.valid_from

        if item.valid_to and (
            not aggregated_metadata.valid_to
            or item.valid_to > aggregated_metadata.valid_to
        ):
            aggregated_metadata.valid_to = item.valid_to

    return aggregated_metadata


def calculate_unique_counts(
    data_catalogues: list[FaresDataCatalogueMetadata],
) -> tuple[int, int, int]:
    """
    Calculates the unique counts from data_catalogues
    """
    unique_product_types: set[str] = set()
    unique_user_types: set[str] = set()

    for catalogue in data_catalogues:
        if catalogue.product_type:
            unique_product_types.update(catalogue.product_type)
        if catalogue.user_type:
            unique_user_types.update(catalogue.user_type)

    pass_product_values = ["dayPass", "periodPass"]
    trip_product_values = [
        "singleTrip",
        "dayReturnTrip",
        "periodReturnTrip",
        "timeLimitedSingleTrip",
        "shortTrip",
    ]

    unique_pass_products = [t for t in unique_product_types if t in pass_product_values]
    unique_trip_products = [t for t in unique_product_types if t in trip_product_values]

    log.info(
        "Calculated Unique Counts across Fares Datacatalogue",
        unique_user_types=unique_user_types,
        unique_pass_products=unique_pass_products,
        unique_trip_products=unique_trip_products,
    )
    return (
        len(unique_user_types),
        len(unique_pass_products),
        len(unique_trip_products),
    )


def aggregate_metadata(
    metadata_items: list[FaresMetadata],
    data_catalogues: list[FaresDataCatalogueMetadata],
) -> FaresMetadata:
    """
    Aggregates metadata items into a single FaresMetadata with unique counts for
    user profiles, trip products, and pass products across data catalogues
    """
    aggregated_metadata = sum_metadata_fields(metadata_items)

    user_profiles_count, pass_products_count, trip_products_count = (
        calculate_unique_counts(data_catalogues)
    )

    aggregated_metadata.num_of_user_profiles = user_profiles_count
    aggregated_metadata.num_of_pass_products = pass_products_count
    aggregated_metadata.num_of_trip_products = trip_products_count

    log.info(
        "Aggregated Metadata",
        **asdict(aggregated_metadata),
    )
    return aggregated_metadata


def map_metadata(metadata_items: list[dict[str, Any]]) -> tuple[
    list[FaresMetadata],
    list[FaresDataCatalogueMetadata],
    list[FaresMetadataStop],
    list[str],
]:
    """
    Map dynamo response to Fares Models
    """
    fares_metadata_list: list[FaresMetadata] = []
    data_catalogue_list: list[FaresDataCatalogueMetadata] = []
    stop_ids: set[int] = set()
    netex_schema_versions: set[str] = set()
    type_deserializer = TypeDeserializer()
    log.info("Processing Metadata into DB Objects", count=len(metadata_items))
    for item in metadata_items:
        metadata_item = type_deserializer.deserialize(item["Metadata"])
        metadata_item.pop("datasetmetadata_ptr_id", None)

        data_catalogue_item = type_deserializer.deserialize(item["DataCatalogue"])
        data_catalogue_item.pop("fares_metadata_id", None)
        data_catalogue_item.pop("id", None)

        netex_schema_version = type_deserializer.deserialize(
            item.get("NetexSchemaVersion", {"S": "1.1"})
        )

        stop_ids.update(stop for stop in type_deserializer.deserialize(item["StopIds"]))
        netex_schema_versions.add(netex_schema_version)
        fares_metadata_list.append(FaresMetadata(**metadata_item))
        data_catalogue_list.append(FaresDataCatalogueMetadata(**data_catalogue_item))

    stops = [FaresMetadataStop(stoppoint_id=stop_id) for stop_id in stop_ids]
    log.info(
        "Metadata Mapping Completed",
        fares_metadata_count=len(fares_metadata_list),
        data_catalogue_count=len(data_catalogue_list),
        stops_count=len(stops),
        netex_schema_versions_count=len(netex_schema_versions),
    )
    return (
        fares_metadata_list,
        data_catalogue_list,
        stops,
        list(netex_schema_versions),
    )
