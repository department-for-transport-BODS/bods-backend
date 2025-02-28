"""
Setup organisation dataset metadata tables
"""

from common_layer.database.client import SqlDB
from common_layer.database.models.model_organisation import OrganisationDatasetMetadata
from common_layer.database.repos.repo_fares import (
    FaresDataCatalogueMetadataRepo,
    FaresMetadataRepo,
    FaresMetadataStopsRepo,
)
from common_layer.database.repos.repo_organisation import OrganisationDatasetMetdataRepo


def load_dataset(revision_id: int, schema_version: str, db: SqlDB) -> int:
    """
    Load dataset metadata
    """
    dataset_metadata_repo = OrganisationDatasetMetdataRepo(db)
    fares_metadata_repo = FaresMetadataRepo(db)
    fares_metadata_stops_repo = FaresMetadataStopsRepo(db)
    fares_data_catalogue_repo = FaresDataCatalogueMetadataRepo(db)

    dataset_metadata = dataset_metadata_repo.get_by_revision_id(revision_id)
    metadata_id = dataset_metadata.id if dataset_metadata else None

    if metadata_id:
        fares_data_catalogue_repo.delete_by_metadata_id(metadata_id)
        fares_metadata_stops_repo.delete_by_metadata_id(metadata_id)
        fares_metadata_repo.delete_by_metadata_id(metadata_id)
    else:
        metadata_id = dataset_metadata_repo.insert(
            OrganisationDatasetMetadata(
                revision_id=revision_id, schema_version=schema_version
            )
        ).id

    return metadata_id
