"""
DynamoDB Data Loader Client
"""

import asyncio
import random
import time
from typing import Any, Literal, NotRequired, TypedDict

import boto3
from boto3.dynamodb.types import TypeDeserializer
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

    batch_size: int = 25
    deserializer = TypeDeserializer()

    def __init__(
        self,
        table_name: str,
        region: str = "eu-west-2",
        partition_key: str = "AtcoCode",
        max_concurrent_batches: int | None = None,
    ):
        """Initialize DynamoDB loader with table name and region."""
        self.dynamodb = boto3.resource("dynamodb", region_name=region)  # type: ignore
        self.table_name = table_name
        self.table = self.dynamodb.Table(table_name)
        self.log = get_logger().bind(table_name=table_name)
        self.partition_key = partition_key
        self.max_concurrent_batches = (
            max_concurrent_batches if max_concurrent_batches else 30
        )
        self.semaphore = asyncio.Semaphore(self.max_concurrent_batches)

    def prepare_put_requests(
        self, items: list[dict[str, Any]]
    ) -> BatchWriteItemInputRequestItems:
        """
        Convert items into DynamoDB put request format.
        """
        write_requests: list[WriteRequestTypeDef] = []

        for item in items:
            if self.partition_key not in item:
                self.log.warning(
                    "Skipping item missing partition key",
                    partition_key=self.partition_key,
                    item_keys=list(item.keys()),
                )
                continue

            write_request: WriteRequestTypeDef = {"PutRequest": {"Item": item}}
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
                "DeleteRequest": {"Key": {self.partition_key: item[self.partition_key]}}
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
                error_message = error_response.get("Error", {}).get("Message", "")
                error_code = error_response.get("Error", {}).get("Code", "")
                self.log.error(
                    "Failed to execute batch write operation",
                    error_code=error_code,
                    retry_count=retry_count,
                    operation=operation,
                    error_message=error_message,
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

    async def async_process_batch(self, items: list[dict[str, Any]]) -> int:
        """
        Process a single batch of items with retries.
        Semaphore is used to limit the concurrent executions
        """
        if not items:
            return 0

        request_items = self.prepare_put_requests(items)
        max_retries = 5
        retry_count = 0
        unprocessed_items: BatchWriteItemInputRequestItems = request_items

        async with self.semaphore:
            while unprocessed_items and retry_count < max_retries:
                if retry_count > 0:
                    wait_time = (2**retry_count) * 0.1 + (random.random() * 0.1)
                    await self.log.ainfo(
                        "Retrying batch operation",
                        retry_count=retry_count,
                        wait_time=wait_time,
                        remaining_items=len(unprocessed_items),
                    )
                    await asyncio.sleep(wait_time)

                try:
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.dynamodb.meta.client.batch_write_item(
                            RequestItems=unprocessed_items
                        ),
                    )
                    unprocessed_items = response.get("UnprocessedItems", {})
                    retry_count += 1

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")
                    if error_code == "ProvisionedThroughputExceededException":
                        retry_count += 1
                        await asyncio.sleep(2**retry_count * 0.1)
                        continue
                    raise

        return len(unprocessed_items)

    async def async_batch_write_items(
        self, items: list[dict[str, Any]]
    ) -> tuple[int, int]:
        """
        Write items in parallel batches
         returning (processed_count, error_count)."""
        if not items:
            return 0, 0

        # Split items into batches of batch_size
        batches = [
            items[i : i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]

        tasks = [self.async_process_batch(batch) for batch in batches]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        error_count: int = 0
        for result in results:
            if isinstance(result, BaseException):
                error_count += self.batch_size
                await self.log.aerror("Batch failed", error=str(result))
            else:
                error_count += result
        processed_count = len(items) - error_count

        await self.log.ainfo(
            "Completed batch operation",
            processed_count=processed_count,
            error_count=error_count,
        )

        return processed_count, error_count

    async def async_update_private_codes(
        self, updates: dict[str, int]
    ) -> tuple[int, int]:
        """
        Asynchronously update PrivateCode for multiple AtcoCodes using controlled concurrency.
        Returns:
        - processed_count: Number of successfully updated items
        - failed_count: Number of items that failed
        """
        if not updates:
            return 0, 0

        await self.log.ainfo(
            "Updating PrivateCodes for DynamoDB records", batch_size=len(updates)
        )

        processed_count = 0
        error_count = 0
        # Dynamo transact_write_items can handle up to 100 updates at a time
        batch_size = 100

        batches = [
            dict(list(updates.items())[i : i + batch_size])
            for i in range(0, len(updates), batch_size)
        ]
        tasks = [self.update_private_codes_batch(batch) for batch in batches]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        processed_count = sum(
            len(batch) for batch, success in zip(batches, results) if success
        )
        error_count = sum(
            len(batch) for batch, success in zip(batches, results) if not success
        )

        await self.log.ainfo(
            "Completed batch update operations",
            processed_count=processed_count,
            error_count=error_count,
            total_time=f"{total_time:.2f}s",
        )

        return processed_count, error_count

    async def update_private_codes_batch(self, batch: dict[str, int]) -> bool:
        """
        Updates multiple AtcoCodes in DynamoDB using transact_write_items with retries.
        Each batch can contain up to 100 updates.
        If a batch fails, it retries with exponential backoff.

        Returns:
        - True if update was successful after all retries
        - False if update failed after max retries
        """
        if not batch:
            return False

        transact_items = [
            {
                "Update": {
                    "TableName": self.table_name,
                    "Key": {self.partition_key: atco_code},
                    "UpdateExpression": "SET PrivateCode = :private_code",
                    "ExpressionAttributeValues": {":private_code": str(private_code)},
                }
            }
            for atco_code, private_code in batch.items()
        ]

        max_retries = 5
        retry_count = 0

        async with self.semaphore:
            while retry_count < max_retries:
                if retry_count > 0:
                    wait_time = (2**retry_count) * 0.1 + (random.random() * 0.1)
                    await self.log.awarning(
                        "Retrying transact_write_items due to failure",
                        retry_attempt=retry_count,
                        wait_time=f"{wait_time:.2f}s",
                    )
                    await asyncio.sleep(wait_time)

                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: self.dynamodb.meta.client.transact_write_items(
                            TransactItems=transact_items  # type: ignore
                        ),
                    )
                    return True

                except ClientError as e:
                    error_response: _ClientErrorResponseTypeDef = e.response
                    error_message = error_response.get("Error", {}).get("Message", "")
                    error_code = error_response.get("Error", {}).get("Code", "")
                    await self.log.aerror(
                        "Failed to execute batch write operation",
                        error_code=error_code,
                        retry_count=retry_count,
                        error_message=error_message,
                    )
                    if error_code in [
                        "ProvisionedThroughputExceededException",
                        "RequestLimitExceeded",
                    ]:
                        retry_count += 1
                        continue

                    await self.log.aerror(
                        "Failed to update batch", error_code=error_code, error=str(e)
                    )
                    return False

        await self.log.aerror("Max retries reached for batch update")
        return False

    async def async_transact_write_items(
        self, items: list[dict[str, Any]]
    ) -> tuple[int, int]:
        """
        Asynchronously write multiple items using TransactWriteItems.
        Can handle up to 100 items per transaction (vs 25 for batch_write).
        All items in a single transaction either succeed or fail together.

        Returns:
        tuple[int, int]: (processed_count, error_count)
        """
        if not items:
            return 0, 0

        await self.log.ainfo(
            "Writing items using TransactWriteItems", item_count=len(items)
        )

        processed_count = 0
        error_count = 0
        # DynamoDB transact_write_items can handle up to 100 items per transaction
        transaction_size = 100

        # Split items into batches of transaction_size
        batches = [
            items[i : i + transaction_size]
            for i in range(0, len(items), transaction_size)
        ]
        tasks = [self.transact_write_items_batch(batch) for batch in batches]

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                error_count += len(batches[i])
                await self.log.aerror("Transaction failed", error=str(result))
            elif result is True:
                processed_count += len(batches[i])
            else:
                error_count += len(batches[i])

        await self.log.ainfo(
            "Completed transact write operations",
            processed_count=processed_count,
            error_count=error_count,
            total_time=f"{total_time:.2f}s",
        )

        return processed_count, error_count

    async def transact_write_items_batch(self, batch: list[dict[str, Any]]) -> bool:
        """
        Writes multiple items in DynamoDB using transact_write_items with retries.
        Each batch can contain up to 100 items.

        Parameters:
        batch (list[dict[str, Any]]): Batch of items to write in a single transaction

        Returns:
        bool: True if write was successful after all retries, False otherwise
        """
        if not batch:
            return False

        transact_items: list[dict[str, Any]] = []

        for item in batch:
            if self.partition_key not in item:
                await self.log.awarning(
                    "Skipping item missing partition key",
                    partition_key=self.partition_key,
                    item_keys=list(item.keys()),
                )
                continue

            transact_items.append(
                {
                    "Put": {
                        "TableName": self.table_name,
                        "Item": item,
                    }
                }
            )

        if not transact_items:
            await self.log.awarning(
                "No valid items found for transaction",
                skipped_count=len(batch),
            )
            return False

        max_retries = 5
        retry_count = 0

        async with self.semaphore:
            while retry_count < max_retries:
                if retry_count > 0:
                    wait_time = (2**retry_count) * 0.1 + (random.random() * 0.1)
                    await self.log.awarning(
                        "Retrying transact_write_items due to failure",
                        retry_attempt=retry_count,
                        wait_time=f"{wait_time:.2f}s",
                    )
                    await asyncio.sleep(wait_time)

                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: self.dynamodb.meta.client.transact_write_items(
                            TransactItems=transact_items  # type: ignore
                        ),
                    )
                    return True

                except ClientError as e:
                    error_response: _ClientErrorResponseTypeDef = e.response
                    error_message = error_response.get("Error", {}).get("Message", "")
                    error_code = error_response.get("Error", {}).get("Code", "")
                    await self.log.aerror(
                        "Failed to execute transact_write_items",
                        error_code=error_code,
                        retry_count=retry_count,
                        error_message=error_message,
                    )
                    if error_code in [
                        "ProvisionedThroughputExceededException",
                        "RequestLimitExceeded",
                        "TransactionCanceledException",
                    ]:
                        retry_count += 1
                        continue

                    await self.log.aerror(
                        "Failed to write batch with transact_write_items",
                        error_code=error_code,
                        exc_info=True,
                    )
                    return False

            await self.log.aerror("Max retries reached for transact_write_items batch")
            return False
