from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_fares import FaresDataCatalogueMetadataRepo
from common_layer.xml.netex.models.netex_publication_delivery import (
    PublicationDeliveryStructure,
)

from ..transform.data_catalogue import create_data_catalogue


def load_data_catalogue(
    netex_data: PublicationDeliveryStructure,
    metadata_id: int,
    file_name: str,
    db: SqlDB,
) -> None:
    """
    Load data catalogue
    """
    fares_data_catalogue_metadata_repo = FaresDataCatalogueMetadataRepo(db)

    data_catalogue = create_data_catalogue(netex_data, file_name, metadata_id)

    fares_data_catalogue_metadata_repo.insert(data_catalogue)
