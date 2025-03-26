"""
Setup organisation dataset metadata tables
"""

from common_layer.dynamodb.client import NaptanStopPointDynamoDBClient
from common_layer.dynamodb.client.fares_metadata import (
    DynamoDBFaresMetadata,
    FaresDynamoDBMetadataInput,
)
from common_layer.xml.netex.models.netex_publication_delivery import (
    PublicationDeliveryStructure,
)

from ..transform.data_catalogue import create_data_catalogue
from ..transform.metadata import create_metadata, get_stop_ids


def load_metadata_into_dynamodb(
    netex: PublicationDeliveryStructure,
    task_id: int,
    file_name: str,
) -> None:
    """
    Load metadata into dynamodb
    """
    dynamodb_fares_metadata_client = DynamoDBFaresMetadata()
    dynamodb_naptan_stop_point_client = NaptanStopPointDynamoDBClient()

    metadata = create_metadata(netex)
    stop_ids = get_stop_ids(netex, dynamodb_naptan_stop_point_client)
    data_catalogue = create_data_catalogue(netex, file_name)
    netex_schema_version = netex.version

    dynamodb_fares_metadata_client.put_metadata(
        task_id,
        FaresDynamoDBMetadataInput(
            metadata=metadata,
            data_catalogue=data_catalogue,
            stop_ids=stop_ids,
            file_name=file_name,
            netex_schema_version=netex_schema_version,
        ),
    )
