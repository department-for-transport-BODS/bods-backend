"""
Load fares metadata into database
"""

from common_layer.database.client import SqlDB
from common_layer.database.models.model_fares import FaresMetadata, FaresMetadataStop
from common_layer.database.repos.repo_fares import (
    FaresMetadataRepo,
    FaresMetadataStopsRepo,
)
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.database.repos.repo_organisation import OrganisationDatasetMetdataRepo
from common_layer.xml.netex.models.netex_publication_delivery import (
    PublicationDeliveryStructure,
)

from ..transform.metadata import create_metadata, get_stop_ids


def load_metadata(
    netex_data: PublicationDeliveryStructure,
    revision_id: int,
    metadata_dataset_id: int,
    db: SqlDB,
) -> FaresMetadata:
    """
    Load metadata
    """
    org_metadata_repo = OrganisationDatasetMetdataRepo(db)
    fares_metadata_repo = FaresMetadataRepo(db)
    naptan_stop_point_repo = NaptanStopPointRepo(db)

    org_metadata_repo.update_min_schema_version(netex_data.version, revision_id)
    metadata = create_metadata(netex_data, metadata_dataset_id)
    stop_ids = get_stop_ids(netex_data, naptan_stop_point_repo)

    fares_metadata_repo.update_metadata(metadata)

    load_metadata_stops(stop_ids, metadata_dataset_id, db)

    return metadata


def load_metadata_stops(stop_ids: list[int], metadata_id: int, db: SqlDB) -> None:
    """
    Load metadata stops
    """
    fares_metadata_stops_repo = FaresMetadataStopsRepo(db)
    stops = [
        FaresMetadataStop(faresmetadata_id=metadata_id, stoppoint_id=stop_id)
        for stop_id in stop_ids
    ]

    fares_metadata_stops_repo.batch_insert_stops(stops)
