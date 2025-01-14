"""
DynamoDB Client
"""

import os
import time
from typing import Any, Callable

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from common_layer.exceptions.pipeline_exceptions import PipelineException
from pydantic import Field
from pydantic_settings import BaseSettings
from structlog.stdlib import get_logger

log = get_logger()


class DynamoDBSettings(BaseSettings):
    """
    Custom settings for DynamoDB
    """

    DYNAMODB_ENDPOINT_URL: str = Field(
        default="http://host.docker.internal:4566",
        description="Endpoint URL for DynamoDB",
    )
    DYNAMODB_TABLE_NAME: str = Field(
        default="",
        description="Table Name for DynamoDB",
    )
    AWS_REGION: str = Field(
        default="eu-west-2",
        description="AWS Region for DynamoDB Table",
    )


class DynamoDB:
    """
    Client for interacting with DynamoDB
    """

    def __init__(self, settings: DynamoDBSettings | None = None):
        self._settings: DynamoDBSettings = settings if settings else DynamoDBSettings()
        self._client = self._create_dynamodb_client()
        self._serializer = TypeSerializer()
        self._deserializer = TypeDeserializer()

    def _create_dynamodb_client(self):
        """
        Create a DynamoDB client
        If running locally, it points to the LocalStack DynamoDB service.
        """
        if os.environ.get("PROJECT_ENV") == "local":
            return boto3.client(
                "dynamodb",
                endpoint_url=self._settings.DYNAMODB_ENDPOINT_URL,
                aws_access_key_id="dummy",
                aws_secret_access_key="dummy",
                region_name=self._settings.AWS_REGION,
            )

        return boto3.client("dynamodb")

    def get_or_compute(
        self, key: str, compute_fn: Callable[[], Any], ttl: int | None = None
    ) -> Any:
        """
        Get a value from cache or compute it and cache it if not found.
        """
        cached_value = self.get(key)

        if cached_value is not None:
            log.info("DynamoDB: Cache hit", key=key)
            return cached_value

        log.info("DynamoDB: Cache miss, computing value", key=key)
        computed_value = compute_fn()

        self.put(key, computed_value, ttl=ttl)

        return computed_value

    def get(self, key: str) -> dict[str, Any] | None:
        """
        Retrieve an item from the DynamoDB table by key.
        """
        try:
            response = self._client.get_item(
                TableName=self._settings.DYNAMODB_TABLE_NAME, Key={"Key": {"S": key}}
            )
            item = response.get("Item", {})
            item_value = item.get("Value", None)
            result = self._deserializer.deserialize(item_value) if item_value else None
            return result
        except Exception as e:
            message = f"Failed to get item with key '{key}': {str(e)}"
            log.error("DynamoDB: Failed ot get item", key=key)
            raise PipelineException(message) from e

    def put(self, key: str, value: Any, ttl: int | None = None):
        """
        Store a value in the DynamoDB table with (optional) TTL.
        """
        try:
            serialized_value = self._serializer.serialize(value)
            item = {
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
