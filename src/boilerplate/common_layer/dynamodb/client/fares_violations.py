"""
DynamoDB Cache Client
"""

from typing import Any

from common_layer.database.models.model_fares import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
)
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

from ..models import FaresViolation
from .base import DynamoDB
from .settings import DynamoBaseSettings, DynamoDBSettings

log = get_logger()


class DynamoDbFaresViolationsSettings(DynamoBaseSettings):
    """
    Settings for DynamoDBFaresViolations client
    """

    DYNAMODB_FARES_VIOLATIONS_TABLE_NAME: str = Field(
        default="",
        description="Table Name for DynamoDB fares violations table",
    )


class DynamoDBFaresViolations(DynamoDB):
    """
    Client for interacting with DynamoDB fares violations table
    """

    def __init__(self, settings: DynamoDbFaresViolationsSettings | None = None):
        fares_metadata_settings = (
            settings if settings else DynamoDbFaresViolationsSettings()
        )
        super().__init__(
            DynamoDBSettings(
                DYNAMODB_ENDPOINT_URL=fares_metadata_settings.DYNAMODB_ENDPOINT_URL,
                AWS_REGION=fares_metadata_settings.AWS_REGION,
                DYNAMODB_TABLE_NAME=fares_metadata_settings.DYNAMODB_FARES_VIOLATIONS_TABLE_NAME,
                PROJECT_ENV=fares_metadata_settings.PROJECT_ENV,
            )
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
                "SK": self._serializer.serialize(file_name),
                "Violations": self._serializer.serialize(
                    [violation.__dict__ for violation in violations]
                ),
            },
        )

    def get_violations(
        self,
        task_id: int,
    ) -> list[dict[str, Any]]:
        """
        Get metadata from dynamodb
        """
        query_params: dict[str, Any] = {
            "TableName": self._settings.DYNAMODB_TABLE_NAME,
            "KeyConditionExpression": "PK = :task_id",
            "ExpressionAttributeValues": {
                ":task_id": self._serializer.serialize(task_id)
            },
        }

        metadata_items: list[dict[str, Any]] = []
        metadata_response = self._client.query(**query_params)
        metadata_items.extend(metadata_response.get("Items", []))

        while "LastEvaluatedKey" in metadata_response:
            query_params["ExclusiveStartKey"] = metadata_response["LastEvaluatedKey"]
            metadata_response = self._client.query(**query_params)

            metadata_items.extend(metadata_response.get("Items", []))

        return metadata_items
