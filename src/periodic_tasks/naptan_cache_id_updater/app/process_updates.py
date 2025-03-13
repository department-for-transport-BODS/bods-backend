"""
Async logic for processing NaPTAN Stop Point Private Code (ID) updates
"""

import asyncio

from botocore.exceptions import ClientError
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.dynamodb.client_loader import DynamoDBLoader
from structlog.stdlib import get_logger

# Number of IDs to fetch per batch
# Adjust if necessary for performance tuning
BATCH_SIZE = 10000

log = get_logger()


async def process_batch(
    atco_code_id_map: dict[str, int],
    dynamo_loader: DynamoDBLoader,
) -> tuple[int, int]:
    """Fetch corresponding IDs from Postgres and update in DynamoDB."""
    if not atco_code_id_map:
        log.warning("atco_code_id_map empty")
        return 0, 0
    return await dynamo_loader.async_update_private_codes(atco_code_id_map)


async def process_private_code_updates(
    dynamo_loader: DynamoDBLoader, naptan_repo: NaptanStopPointRepo
) -> tuple[int, int]:
    """
    Update the PrivateCodes for StopPoints in batches with controlled concurrency.
    """
    total_processed = 0
    total_errors = 0
    active_tasks: list[asyncio.Task[tuple[int, int]]] = []

    async def wait_for_slot() -> None:
        """Wait for a task slot to become available and process completed tasks."""
        nonlocal total_processed, total_errors, active_tasks

        # Wait for at least one task to complete if the limit is reached
        done, pending = await asyncio.wait(
            active_tasks, return_when=asyncio.FIRST_COMPLETED
        )

        for completed_task in done:
            try:
                processed, errors = await completed_task
                total_processed += processed
                total_errors += errors
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", "No message")
                log.error(
                    "AWS operation failed",
                    error_code=error_code,
                    error_message=error_message,
                )
                total_errors += dynamo_loader.batch_size
            except ValueError as e:
                log.error("Failed to process batch result", error=str(e))
                total_errors += dynamo_loader.batch_size

        active_tasks = list(pending)

    try:
        for atco_batch in naptan_repo.stream_naptan_ids(batch_size=BATCH_SIZE):
            log.info("Processing atco batch from Bods DB", batch_size=len(atco_batch))
            if not atco_batch:
                continue

            # Ensure we do not exceed max_concurrent_batches
            while len(active_tasks) >= dynamo_loader.max_concurrent_batches:
                await wait_for_slot()

            task = asyncio.create_task(process_batch(atco_batch, dynamo_loader))
            active_tasks.append(task)

        # Process any remaining active tasks
        while active_tasks:
            await wait_for_slot()

    except Exception:
        log.error("Failed to process private code updates", exc_info=True)
        raise

    log.info(
        "Completed updating Naptan StopPoint IDs",
        processed_count=total_processed,
        error_count=total_errors,
    )

    return total_processed, total_errors
