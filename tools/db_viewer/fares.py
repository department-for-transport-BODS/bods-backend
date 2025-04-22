"""
Dump Fares Data to CSV
"""

from pathlib import Path

from common_layer.database.client import SqlDB
from common_layer.database.models import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
    FaresMetadataStop,
    FaresValidation,
    FaresValidationResult,
    OrganisationDatasetMetadata,
)
from common_layer.database.repos import (
    FaresDataCatalogueMetadataRepo,
    FaresMetadataRepo,
    FaresMetadataStopsRepo,
    FaresValidationRepo,
    FaresValidationResultRepo,
    OrganisationDatasetMetdataRepo,
)

from .organisation import extract_org_info
from .utils import csv_extractor


@csv_extractor()
def extract_fares_validation(db: SqlDB, revision_id: int) -> list[FaresValidation]:
    """
    Extract TXC file attributes from DB.
    """
    repo = FaresValidationRepo(db)
    return repo.get_by_revision_id(revision_id=revision_id)


@csv_extractor()
def extract_fares_validation_result(
    db: SqlDB, revision_id: int
) -> list[FaresValidationResult]:
    """
    Extract TXC file attributes from DB.
    """
    repo = FaresValidationResultRepo(db)
    return repo.get_by_revision_id(revision_id=revision_id)


@csv_extractor()
def extract_dataset_metadata(
    db: SqlDB, revision_id: int
) -> OrganisationDatasetMetadata | None:
    """
    Extract TXC file attributes from DB.
    """
    repo = OrganisationDatasetMetdataRepo(db)
    return repo.get_by_revision_id(revision_id=revision_id)


@csv_extractor()
def extract_fares_metadata(db: SqlDB, dataset_metadata_id: int) -> FaresMetadata | None:
    """
    Extract Fares Metadata by Dataaset Metadata
    """
    repo = FaresMetadataRepo(db)
    return repo.get_by_metadata_id(metadata_id=dataset_metadata_id)


@csv_extractor()
def extract_fares_stops(db: SqlDB, fares_metadata_id: int) -> list[FaresMetadataStop]:
    """
    Extract Fares Stops by Fares Metadata ID
    """
    repo = FaresMetadataStopsRepo(db)
    return repo.get_by_metadata_id(metadata_id=fares_metadata_id)


@csv_extractor()
def extract_data_catalog_metadata(
    db: SqlDB, fares_metadata_id: int
) -> list[FaresDataCatalogueMetadata]:
    """
    Extract Fares Data Catalogue Metadata by Fares Metadata ID
    """
    repo = FaresDataCatalogueMetadataRepo(db)
    return repo.get_by_metadata_id(metadata_id=fares_metadata_id)


def fares_from_revision_id(
    db: SqlDB,
    revision_id: int,
    output_path: Path,
) -> None:
    """
    Output Fares data by Revision ID
    """
    extract_org_info(db, revision_id, output_path=output_path)
    extract_fares_validation(db, revision_id, output_path=output_path)
    extract_fares_validation_result(db, revision_id, output_path=output_path)
    dataset_metadata = extract_dataset_metadata(
        db, revision_id, output_path=output_path
    )
    if dataset_metadata:
        fares_metadata = extract_fares_metadata(
            db, dataset_metadata.id, output_path=output_path
        )
        if fares_metadata:
            extract_fares_stops(
                db, fares_metadata.datasetmetadata_ptr_id, output_path=output_path
            )
            extract_data_catalog_metadata(
                db, fares_metadata.datasetmetadata_ptr_id, output_path=output_path
            )
