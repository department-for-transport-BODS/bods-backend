"""
Setup organisation dataset metadata tables
"""

from common_layer.database.client import SqlDB
from common_layer.database.models.model_organisation import OrganisationDatasetMetadata
from common_layer.database.repos.repo_fares import (
    FaresDataCatalogueMetadataRepo,
    FaresMetadataRepo,
    FaresMetadataStopsRepo,
    FaresValidationRepo,
    FaresValidationResultRepo,
)
from common_layer.database.repos.repo_organisation import OrganisationDatasetMetdataRepo


def load_dataset(db: SqlDB, revision_id: int, schema_version: str) -> int:
    """
    Load dataset metadata
    """
    dataset_metadata_repo = OrganisationDatasetMetdataRepo(db)
    fares_metadata_repo = FaresMetadataRepo(db)
    fares_metadata_stops_repo = FaresMetadataStopsRepo(db)
    fares_data_catalogue_repo = FaresDataCatalogueMetadataRepo(db)
    fares_validation_repo = FaresValidationRepo(db)
    fares_validation_result_repo = FaresValidationResultRepo(db)

    dataset_metadata = dataset_metadata_repo.get_by_revision_id(revision_id)
    metadata_id = dataset_metadata.id if dataset_metadata else None

    fares_validation_repo.delete_by_revision_id(revision_id)
    fares_validation_result_repo.delete_by_revision_id(revision_id)

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
