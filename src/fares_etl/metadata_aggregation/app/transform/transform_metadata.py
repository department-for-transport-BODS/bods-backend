"""
Transform fares metadata items
"""

from boto3.dynamodb.types import TypeDeserializer
from common_layer.database.models.model_fares import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
    FaresMetadataStop,
)


def get_min_schema_version(schema_versions: list[str]) -> str:
    """
    Returns the lowest schema version in list
    """
    return min(schema_versions)


def aggregate_metadata(metadata_items: list[FaresMetadata]) -> FaresMetadata:
    """
    Aggregates metadata items into a single FaresMetadata
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

    for item in metadata_items:
        for field in [
            "num_of_fare_products",
            "num_of_fare_zones",
            "num_of_lines",
            "num_of_pass_products",
            "num_of_sales_offer_packages",
            "num_of_trip_products",
            "num_of_user_profiles",
        ]:
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


def map_metadata(metadata_items: list[dict]):
    """
    Map dynamo response to Fares Models
    """
    fares_metadata_list: list[FaresMetadata] = []
    data_catalogue_list: list[FaresDataCatalogueMetadata] = []
    stop_ids: set[int] = set()
    netex_schema_versions: set[str] = set()
    type_deserializer = TypeDeserializer()

    for item in metadata_items:
        metadata_item = type_deserializer.deserialize(item["Metadata"])
        metadata_item.pop("datasetmetadata_ptr_id")

        data_catalogue_item = type_deserializer.deserialize(item["DataCatalogue"])
        data_catalogue_item.pop("fares_metadata_id")
        data_catalogue_item.pop("id")

        netex_schema_version = type_deserializer.deserialize(
            item.get("NetexSchemaVersion", {"S": "1.1"})
        )

        stop_ids.update(stop for stop in type_deserializer.deserialize(item["StopIds"]))
        netex_schema_versions.add(netex_schema_version)
        fares_metadata_list.append(FaresMetadata(**metadata_item))
        data_catalogue_list.append(FaresDataCatalogueMetadata(**data_catalogue_item))

    stops = [FaresMetadataStop(stoppoint_id=stop_id) for stop_id in stop_ids]

    return (
        fares_metadata_list,
        data_catalogue_list,
        stops,
        list(netex_schema_versions),
    )
