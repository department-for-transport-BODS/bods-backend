"""
Setup organisation dataset metadata tables
"""

from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.dynamodb.client.fares_metadata import DynamoDBFaresMetadata
from common_layer.xml.netex.models.netex_publication_delivery import (
    PublicationDeliveryStructure,
)

from ..transform.data_catalogue import create_data_catalogue
from ..transform.metadata import create_metadata, get_stop_ids


def load_metadata_into_dynamodb(
    netex: PublicationDeliveryStructure,
    task_id: int,
    file_name: str,
    db: SqlDB,
) -> None:
    """
    Load metadata into dynamodb
    """
    dynamodb_fares_metadata_repo = DynamoDBFaresMetadata()
    naptan_stop_point_repo = NaptanStopPointRepo(db)

    metadata = create_metadata(netex)
    stop_ids = get_stop_ids(netex, naptan_stop_point_repo)
    data_catalogue = create_data_catalogue(netex, file_name)
    netex_schema_version = netex.version

    dynamodb_fares_metadata_repo.put_metadata(
        task_id,
        file_name,
        metadata,
        stop_ids,
        data_catalogue,
        netex_schema_version,
    )
