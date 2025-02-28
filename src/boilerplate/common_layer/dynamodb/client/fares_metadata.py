"""
DynamoDB Cache Client
"""

from common_layer.database.models.model_fares import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
)
from pydantic import BaseModel, Field
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


class FaresDynamoDBMetadataInput(BaseModel):
    """
    Inputs for inserting metadata into dynamodb
    """

    metadata: FaresMetadata
    data_catalogue: FaresDataCatalogueMetadata
    stop_ids: list[int]
    file_name: str
    netex_schema_version: str


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

    def put_metadata(self, task_id: int, fares_metadata: FaresDynamoDBMetadataInput):
        """
        Put metadata into dynamodb
        """
        self._client.put_item(
            TableName=self._settings.DYNAMODB_TABLE_NAME,
            ReturnValues="NONE",
            Item={
                "PK": self._serializer.serialize(task_id),
                "SK": self._serializer.serialize(fares_metadata.file_name),
                "Metadata": self._serializer.serialize(
                    fares_metadata.metadata.as_dict()
                ),
                "StopIds": self._serializer.serialize(fares_metadata.stop_ids),
                "DataCatalogue": self._serializer.serialize(
                    fares_metadata.data_catalogue.as_dict()
                ),
                "NetexSchemaVersion": self._serializer.serialize(
                    fares_metadata.netex_schema_version
                ),
            },
        )

    def get_metadata(
        self,
        task_id: int,
    ) -> list[dict]:
        """
        Get metadata from dynamodb
        """
        query_params = {
            "TableName": self._settings.DYNAMODB_TABLE_NAME,
            "KeyConditionExpression": "PK = :task_id",
            "ExpressionAttributeValues": {
                ":task_id": self._serializer.serialize(task_id)
            },
        }

        metadata_items = []
        metadata_response = self._client.query(**query_params)
        metadata_items.extend(metadata_response.get("Items", []))

        while "LastEvaluatedKey" in metadata_response:
            query_params["ExclusiveStartKey"] = metadata_response["LastEvaluatedKey"]
            metadata_response = self._client.query(**query_params)

            metadata_items.extend(metadata_response.get("Items", []))

        return metadata_items
