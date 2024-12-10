import os
import time
from typing import Any, Dict

import boto3
from common_layer.dynamodb.utils import deserialize_dynamo_item, serialize_dynamo_item
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.logger import logger

TABLE_NAME = os.getenv("DYNAMO_DB_TABLE_NAME")


class DynamoDB:

    def __init__(self):
        self._client = self._create_dynamodb_client()

    def _create_dynamodb_client(self):
        """
        Create a DynamoDB client
        If running locally, it points to the LocalStack DynamoDB service.
        """
        if os.environ.get("PROJECT_ENV") == "local":
            return boto3.client(
                "dynamodb",
                endpoint_url="http://host.docker.internal:4566",
                aws_access_key_id="dummy",
                aws_secret_access_key="dummy",
            )
        else:
            return boto3.client("dynamodb")

    def get(self, key: str) -> Dict[str, Any] | None:
        """
        Retrieve an item from the DynamoDB table by key.
        """
        try:
            response = self._client.get_item(
                TableName=TABLE_NAME, Key={"Key": {"S": key}}
            )
            item = response.get("Item", {})
            item_value = item.get("Value", None)
            if item_value:
                result = deserialize_dynamo_item(item_value)
                return result
            logger.info(f"Item with key '{key}' not found in table '{TABLE_NAME}'")
            return None
        except Exception as e:
            message = f"Failed to get item with key '{key}': {str(e)}"
            logger.error(message)
            raise PipelineException(message) from e

    def put(self, key: str, value: Any, ttl: int | None = None):
        """
        Store a value in the DynamoDB table with (optional) TTL.
        """
        try:
            serialized_value = serialize_dynamo_item(value)
            item = {
                "Key": {"S": key},
                "Value": serialized_value,
            }
            if ttl:
                expiration_time = int(time.time()) + ttl
                item["ttl"] = expiration_time

            self._client.put_item(TableName=TABLE_NAME, Item=item)
        except Exception as e:
            message = f"Failed to set item with key '{key}': {str(e)}"
            logger.error(message)
            raise PipelineException(message) from e
