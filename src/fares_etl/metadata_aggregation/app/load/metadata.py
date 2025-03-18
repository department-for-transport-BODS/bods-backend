"""
Load fares metadata into database
"""

from common_layer.database.client import SqlDB
from common_layer.database.models import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
    FaresMetadataStop,
)
from common_layer.database.repos import (
    FaresDataCatalogueMetadataRepo,
    FaresMetadataRepo,
    FaresMetadataStopsRepo,
)


def load_metadata(
    db: SqlDB,
    metadata: FaresMetadata,
    stops: list[FaresMetadataStop],
    data_catalogues: list[FaresDataCatalogueMetadata],
) -> None:
    """
    Load metadata
    """
    fares_metadata_repo = FaresMetadataRepo(db)
    fares_metadata_stops_repo = FaresMetadataStopsRepo(db)
    fares_data_catalogue_metadata_repo = FaresDataCatalogueMetadataRepo(db)

    fares_metadata_repo.insert(metadata)
    fares_metadata_stops_repo.bulk_insert(stops)
    fares_data_catalogue_metadata_repo.bulk_insert(data_catalogues)
