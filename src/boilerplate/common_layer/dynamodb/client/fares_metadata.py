"""
DynamoDB Cache Client
"""

import time
from typing import Any

from common_layer.database.models import FaresDataCatalogueMetadata, FaresMetadata
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

from ..models import FaresViolation
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

    def get_one_day_ttl(self):
        """
        Gets TTL definition for 1 day
        """
        return {"N": str(int(time.time()) + (60 * 60 * 24))}

    def put_metadata(self, task_id: int, fares_metadata: FaresDynamoDBMetadataInput):
        """
        Put metadata into dynamodb
        """
        self._client.put_item(
            TableName=self._settings.DYNAMODB_TABLE_NAME,
            ReturnValues="NONE",
            Item={
                "PK": self._serializer.serialize(task_id),
                "SK": self._serializer.serialize(
                    f"METADATA#{fares_metadata.file_name}"
                ),
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
                "ttl": self.get_one_day_ttl(),
            },
        )

    def put_violations(
        self, task_id: int, file_name: str, violations: list[FaresViolation]
    ):
        """
        Put metadata into dynamodb
        """
        self._client.put_item(
            TableName=self._settings.DYNAMODB_TABLE_NAME,
            ReturnValues="NONE",
            Item={
                "PK": self._serializer.serialize(task_id),
                "SK": self._serializer.serialize(f"VIOLATION#{file_name}"),
                "FileName": self._serializer.serialize(file_name),
                "Violations": self._serializer.serialize(
                    [vars(violation) for violation in violations]
                ),
                "ttl": self.get_one_day_ttl(),
            },
        )

    def get_all_data_for_task(
        self,
        task_id: int,
    ) -> list[dict[str, Any]]:
        """
        Get data for given task id from dynamodb
        """
        query_params: dict[str, Any] = {
            "TableName": self._settings.DYNAMODB_TABLE_NAME,
            "KeyConditionExpression": "PK = :task_id",
            "ExpressionAttributeValues": {
                ":task_id": self._serializer.serialize(task_id)
            },
        }

        items: list[dict[str, Any]] = []
        response = self._client.query(**query_params)
        items.extend(response.get("Items", []))

        while "LastEvaluatedKey" in response:
            query_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = self._client.query(**query_params)

            items.extend(response.get("Items", []))

        return items
