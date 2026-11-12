"""
DynamoDB Client
"""

import time
from typing import TYPE_CHECKING, Any

import boto3
import botocore.config
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from common_layer.database.client import ProjectEnvironment
from common_layer.exceptions.pipeline_exceptions import PipelineException
from structlog.stdlib import get_logger

from .models import AttributeValueTypeDef
from .settings import DynamoDBSettings

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient
log = get_logger()


class DynamoDB:
    """
    Client for interacting with DynamoDB
    """

    def __init__(self, settings: DynamoDBSettings | None = None):
        self._settings: DynamoDBSettings = settings if settings else DynamoDBSettings()
        self._client = self._create_dynamodb_client()
        self._serializer = TypeSerializer()
        self._deserializer = TypeDeserializer()

    def _create_dynamodb_client(self) -> "DynamoDBClient":
        """
        Create a DynamoDB client
        If running locally, it points to the LocalStack DynamoDB service.
        """
        if self._settings.PROJECT_ENV == ProjectEnvironment.LOCAL:
            return boto3.client(  # type: ignore
                "dynamodb",
                endpoint_url=self._settings.DYNAMODB_ENDPOINT_URL,
                aws_access_key_id="dummy",
                aws_secret_access_key="dummy",
                region_name=self._settings.AWS_REGION,
            )

        config = botocore.config.Config(proxies={})
        return boto3.client("dynamodb", config=config)  # type: ignore

    def get(self, key: str) -> dict[str, Any] | None:
        """
        Retrieve an item from the DynamoDB table by key.
        """
        try:
            response = self._client.get_item(
                TableName=self._settings.DYNAMODB_TABLE_NAME,
                Key={"Key": {"S": key}},
            )
            item = response.get("Item", {})
            item_value = item.get("Value", None)
            result = self._deserializer.deserialize(item_value) if item_value else None
            return result
        except Exception as e:
            message = f"Failed to get item with key '{key}': {str(e)}"
            log.error("DynamoDB: Failed to get item", key=key)
            raise PipelineException(message) from e

    def put(self, key: str, value: Any, ttl: int | None = None):
        """
        Store a value in the DynamoDB table with (optional) TTL.
        """
        try:
            serialized_value: AttributeValueTypeDef = self._serializer.serialize(value)
            item: dict[str, str | AttributeValueTypeDef] = {
                "Key": {"S": key},
                "Value": serialized_value,
            }
            if ttl:
                expiration_time = int(time.time()) + ttl
                item["ttl"] = {"S": str(expiration_time)}

            self._client.put_item(
                TableName=self._settings.DYNAMODB_TABLE_NAME, Item=item
            )
        except Exception as e:
            message = f"Failed to set item with key '{key}': {str(e)}"
            log.error("Failed to set item", key=key, exc_info=True)
            raise PipelineException(message) from e
