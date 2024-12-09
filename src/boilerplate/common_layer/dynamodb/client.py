import logging
import os
import time
from typing import Any, Dict

import boto3
from common_layer.dynamodb.utils import deserialize_dynamo_item, serialize_dynamo_item
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.logger import logger

TABLE_NAME = os.getenv("DYNAMO_DB_TABLE_NAME")


class DynamoDB:

    _client = None

    @staticmethod
    def client():
        """
        Returns the DynamoDB client, initializing it if it doesn't exist.
        """
        if DynamoDB._client is None:
            DynamoDB._client = DynamoDB._create_dynamodb_client()
        return DynamoDB._client

    @staticmethod
    def _create_dynamodb_client():
        """
        Creates a DynamoDB client with the boto3.resource API
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
            return boto3.resource("dynamodb")

    @staticmethod
    def get(key: str) -> Dict[str, Any] | None:
        """
        Retrieve an item from the DynamoDB table by key.

        :param key: The partition key for the item.
        :return: The item as a JSON object (dict), or None if not found.
        """
        try:
            client = DynamoDB.client()
            response = client.get_item(TableName=TABLE_NAME, Key={"Key": {"S": key}})
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

    @staticmethod
    def put(key: str, value: Dict[str, Any], ttl: int | None = None):
        """
        Store a JSON object in the DynamoDB table with a TTL.

        :param key: The partition key for the item.
        :param value: The value to store as a JSON object (dict).
        :param ttl: The time-to-live for the item (in seconds from now).
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

            client = DynamoDB.client()
            client.put_item(TableName=TABLE_NAME, Item=item)
        except Exception as e:
            message = f"Failed to set item with key '{key}': {str(e)}"
            logger.error(message)
            raise PipelineException(message) from e
