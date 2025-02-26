"""
Setup metadata tables to import fares data into
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.models.model_organisation import OrganisationDatasetMetadata
from common_layer.database.repos.repo_fares import (
    FaresDataCatalogueMetadataRepo,
    FaresMetadataRepo,
    FaresMetadataStopsRepo,
)
from common_layer.database.repos.repo_organisation import OrganisationDatasetMetdataRepo
from pydantic import BaseModel, ConfigDict, Field
from structlog import get_logger

log = get_logger()


class SetupMetadataInput(BaseModel):
    """
    Input data for the Setup Metadata Tables Function
    """

    model_config = ConfigDict(populate_by_name=True)

    revision: int = Field(alias="DatasetRevisionId")


def lambda_handler(event: dict[str, Any], _context: LambdaContext):
    """
    Setup metadata tables to import fares data into
    """
    log.debug("Input Data", data=event)

    input_data = SetupMetadataInput(**event)

    db = SqlDB()

    dataset_metadata_repo = OrganisationDatasetMetdataRepo(db)
    fares_metadata_repo = FaresMetadataRepo(db)
    fares_metadata_stops_repo = FaresMetadataStopsRepo(db)
    fares_data_catalogue_repo = FaresDataCatalogueMetadataRepo(db)

    dataset_metadata = dataset_metadata_repo.get_by_revision_id(input_data.revision)
    metadata_id = dataset_metadata.id if dataset_metadata else None

    if metadata_id:
        fares_data_catalogue_repo.delete_by_metadata_id(metadata_id)
        fares_metadata_stops_repo.delete_by_metadata_id(metadata_id)
        fares_metadata_repo.delete_by_metadata_id(metadata_id)
    else:
        metadata_id = dataset_metadata_repo.insert(
            OrganisationDatasetMetadata(
                revision_id=input_data.revision,
                schema_version="1.1",
            )
        ).id

    return {
        "statusCode": 200,
        "body": {
            "metadataId": metadata_id,
        },
    }
