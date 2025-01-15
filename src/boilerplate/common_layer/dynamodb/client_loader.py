"""
DynamoDB Data Loader Client
"""

import random
import time
from typing import Any, Literal, NotRequired, TypedDict

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError
from structlog.stdlib import get_logger


class _ClientErrorResponseError(TypedDict, total=False):
    """Error details from a DynamoDB ClientError response."""

    Code: str
    Message: str


class _ResponseMetadataTypeDef(TypedDict):
    """Metadata from a DynamoDB response."""

    RequestId: str
    HostId: str
    HTTPStatusCode: int
    HTTPHeaders: dict[str, Any]
    RetryAttempts: int


class _AttributeMapTypeDef(TypedDict, total=False):
    """Key-value pair for attribute mapping."""

    key: str
    value: Any


class _CancellationReasonTypeDef(TypedDict, total=False):
    """Reason for operation cancellation."""

    Code: str
    Message: str
    Item: _AttributeMapTypeDef


class _ClientErrorResponseTypeDef(TypedDict, total=False):
    """Full structure of a DynamoDB ClientError response."""

    Status: str
    StatusReason: str
    Error: _ClientErrorResponseError
    ResponseMetadata: _ResponseMetadataTypeDef
    CancellationReasons: list[_CancellationReasonTypeDef]


class PutRequestTypeDef(TypedDict):
    """DynamoDB put request format containing a single item to be written."""

    Item: dict[str, Any]


class DeleteRequestTypeDef(TypedDict):
    """DynamoDB delete request format containing the key of the item to be deleted."""

    Key: dict[str, Any]


class WriteRequestTypeDef(TypedDict, total=False):
    """
    DynamoDB write request format for batch operations
    containing either a put or delete request.
    """

    PutRequest: NotRequired[PutRequestTypeDef]
    DeleteRequest: NotRequired[DeleteRequestTypeDef]


class BatchWriteItemOutputTypeDef(TypedDict):
    """DynamoDB batch write operation response format including unprocessed items and metadata."""

    UnprocessedItems: dict[str, list[WriteRequestTypeDef]]
    ConsumedCapacity: NotRequired[list[dict[str, Any]]]
    ResponseMetadata: NotRequired[dict[str, Any]]


BatchWriteItemInputRequestItems = dict[str, list[WriteRequestTypeDef]]
DynamoDBOperation = Literal["put", "delete"]


class DynamoDBLoader:
    """Handles batch writing of items to DynamoDB with retry logic and error handling."""

    def __init__(
        self,
        table_name: str,
        region: str = "eu-west-2",
        partition_key: str = "AtcoCode",
    ):
        """Initialize DynamoDB loader with table name and region."""
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table_name = table_name
        self.table = self.dynamodb.Table(table_name)
        self.batch_size = 25
        self.serializer = TypeSerializer()
        self.deserializer = TypeDeserializer()
        self.log = get_logger().bind(table_name=table_name)
        self.partition_key = partition_key

    def prepare_put_requests(
        self, items: list[dict[str, Any]]
    ) -> BatchWriteItemInputRequestItems:
        """Convert items into DynamoDB put request format."""
        write_requests: list[WriteRequestTypeDef] = []

        for item in items:
            # Validate item has the partition key
            if self.partition_key not in item:
                self.log.warning(
                    "Skipping item missing partition key",
                    partition_key=self.partition_key,
                    item_keys=list(item.keys()),
                )
                continue

            dynamodb_item = {k: self.serializer.serialize(v) for k, v in item.items()}
            write_request: WriteRequestTypeDef = {"PutRequest": {"Item": dynamodb_item}}
            write_requests.append(write_request)

        return {self.table_name: write_requests}

    def prepare_delete_requests(
        self, items: list[dict[str, str]]
    ) -> BatchWriteItemInputRequestItems:
        """Convert items into DynamoDB delete request format."""
        write_requests: list[WriteRequestTypeDef] = []

        for item in items:
            if self.partition_key not in item:
                self.log.warning(
                    "Skipping delete request missing partition key",
                    partition_key=self.partition_key,
                )
                continue

            write_request: WriteRequestTypeDef = {
                "DeleteRequest": {
                    "Key": {
                        self.partition_key: self.serializer.serialize(
                            item[self.partition_key]
                        )
                    }
                }
            }
            write_requests.append(write_request)

        return {self.table_name: write_requests}

    def handle_unprocessed_items(
        self, response: BatchWriteItemOutputTypeDef, operation: DynamoDBOperation
    ) -> list[dict[str, Any]]:
        """Process any items that failed to write and convert back to Python types."""
        unprocessed_items = response.get("UnprocessedItems", {}).get(
            self.table_name, []
        )

        if operation == "put":
            return [
                {
                    k: self.deserializer.deserialize(v)
                    for k, v in item["PutRequest"]["Item"].items()
                }
                for item in unprocessed_items
                if "PutRequest" in item
            ]
        if operation == "delete":
            return [
                {
                    self.partition_key: self.deserializer.deserialize(
                        item["DeleteRequest"]["Key"][self.partition_key]
                    )
                }
                for item in unprocessed_items
                if "DeleteRequest" in item
            ]

        self.log.error(
            "Invalid operation type while handling unprocessed items",
            operation=operation,
            valid_operations=["put", "delete"],
            unprocessed_count=len(unprocessed_items),
        )
        raise ValueError(f"Unknown operation: {operation}. Must be 'put' or 'delete'")

    def batch_write_with_retries(
        self,
        request_items: BatchWriteItemInputRequestItems,
        operation: DynamoDBOperation,
    ) -> list[dict[str, Any]]:
        """Execute batch write operation with exponential backoff retry logic."""
        max_retries = 5
        retry_count = 0
        unprocessed_items = request_items

        while unprocessed_items and retry_count < max_retries:
            if retry_count > 0:
                wait_time = (2**retry_count) * 0.1 + (random.random() * 0.1)
                time.sleep(wait_time)
                self.log.info(
                    "Retrying batch write operation",
                    retry_count=retry_count,
                    wait_time=wait_time,
                    operation=operation,
                )

            try:
                response = self.dynamodb.meta.client.batch_write_item(
                    RequestItems=unprocessed_items
                )
                unprocessed_items = response.get("UnprocessedItems", {})
                retry_count += 1
            except ClientError as e:
                error_response: _ClientErrorResponseTypeDef = e.response
                error_code = error_response.get("Error", {}).get("Code", "")
                self.log.error(
                    "Failed to execute batch write operation",
                    error_code=error_code,
                    retry_count=retry_count,
                    operation=operation,
                )
                if error_code == "ProvisionedThroughputExceededException":
                    retry_count += 1
                    continue
                raise

        return self.handle_unprocessed_items(
            {"UnprocessedItems": unprocessed_items}, operation
        )

    def batch_write_items(
        self, items: list[dict[str, Any]], operation: DynamoDBOperation = "put"
    ) -> list[dict[str, Any]]:
        """Write or delete items in batches, returning any unprocessed items."""
        if not items:
            return []

        self.log.info(
            "Starting batch operation", operation=operation, item_count=len(items)
        )

        if operation == "put":
            request_items = self.prepare_put_requests(items)
        elif operation == "delete":
            request_items = self.prepare_delete_requests(items)
        else:
            self.log.error(
                "Invalid operation type provided",
                operation=operation,
                valid_operations=["put", "delete"],
            )
            raise ValueError(
                f"Unknown operation: {operation}. Must be 'put' or 'delete'"
            )

        result = self.batch_write_with_retries(request_items, operation)

        if result:
            self.log.warning(
                "Completed batch operation with unprocessed items",
                operation=operation,
                unprocessed_count=len(result),
            )
        else:
            self.log.info(
                "Successfully completed batch operation",
                operation=operation,
                processed_count=len(items),
            )

        return result
