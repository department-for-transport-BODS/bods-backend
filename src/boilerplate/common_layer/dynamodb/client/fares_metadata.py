"""
DynamoDB Cache Client
"""

from common_layer.database.models.model_fares import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
)
from pydantic import Field
from structlog.stdlib import get_logger

from .base import DynamoDB
from .settings import DynamoBaseSettings, DynamoDBSettings

log = get_logger()


class DynamoDbFaresMetadataSettings(DynamoBaseSettings):
    """
    Settings for DynamoDBFaresMetadata client
    """

    DYNAMODB_FARES_METADATA_TABLE_NAME: str = Field(
        default="",
        description="Table Name for DynamoDB fares metadata table",
    )


class DynamoDBFaresMetadata(DynamoDB):
    """
    Client for interacting with DynamoDB fares metadata table
    """

    def __init__(self, settings: DynamoDbFaresMetadataSettings | None = None):
        fares_metadata_settings = (
            settings if settings else DynamoDbFaresMetadataSettings()
        )
        super().__init__(
            DynamoDBSettings(
                DYNAMODB_ENDPOINT_URL=fares_metadata_settings.DYNAMODB_ENDPOINT_URL,
                AWS_REGION=fares_metadata_settings.AWS_REGION,
                DYNAMODB_TABLE_NAME=fares_metadata_settings.DYNAMODB_FARES_METADATA_TABLE_NAME,
                PROJECT_ENV=fares_metadata_settings.PROJECT_ENV,
            )
        )

    def put_metadata(
        self,
        task_id: int,
        file_name: str,
        metadata: FaresMetadata,
        stop_ids: list[int],
        data_catalogue: FaresDataCatalogueMetadata,
    ):
        """
        Put metadata into dynamodb
        """
        self._client.put_item(
            TableName=self._settings.DYNAMODB_TABLE_NAME,
            ReturnValues="NONE",
            Item={
                "PK": self._serializer.serialize(task_id),
                "SK": self._serializer.serialize(file_name),
                "Metadata": self._serializer.serialize(metadata.as_dict()),
                "StopIds": self._serializer.serialize(stop_ids),
                "DataCatalogue": self._serializer.serialize(data_catalogue.as_dict()),
            },
        )
