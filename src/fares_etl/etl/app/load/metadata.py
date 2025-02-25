"""
Load fares metadata into database
"""

from common_layer.database.client import SqlDB
from common_layer.database.models.model_fares import FaresMetadataStop
from common_layer.database.repos.repo_fares import (
    FaresMetadataRepo,
    FaresMetadataStopsRepo,
)
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.xml.netex.models.netex_publication_delivery import (
    PublicationDeliveryStructure,
)

from ..transform.metadata import create_metadata, get_stop_ids


def load_metadata(
    netex_data: PublicationDeliveryStructure, metadata_dataset_id: int, db: SqlDB
) -> int:
    """
    Load metadata
    """
    fares_metadata_repo = FaresMetadataRepo(db)
    naptan_stop_point_repo = NaptanStopPointRepo(db)

    metadata = create_metadata(netex_data, metadata_dataset_id)
    stop_ids = get_stop_ids(netex_data, naptan_stop_point_repo)

    metadata_id = fares_metadata_repo.insert(metadata).datasetmetadata_ptr_id

    load_metadata_stops(stop_ids, metadata_id, db)

    return metadata_id


def load_metadata_stops(stop_ids: list[int], metadata_id: int, db: SqlDB) -> None:
    """
    Load metadata stops
    """
    fares_metadata_stops_repo = FaresMetadataStopsRepo(db)
    stops = [
        FaresMetadataStop(faresmetadata_id=metadata_id, stoppoint_id=stop_id)
        for stop_id in stop_ids
    ]

    fares_metadata_stops_repo.bulk_insert(stops)
