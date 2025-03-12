import asyncio
from typing import Any, Dict

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.dynamodb.client_loader import DynamoDBLoader
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

tracer = Tracer()
log = get_logger()

BATCH_SIZE = 5000  # Adjust if necessary for performance tuning


async def process_batch(
    atco_codes: list[str], dynamo_loader: DynamoDBLoader, repo: NaptanStopPointRepo
) -> tuple[int, int]:
    """Fetch corresponding IDs from Postgres and update in DynamoDB."""
    if not atco_codes:
        return 0, 0

    log.info("Fetching IDs from Postgres", batch_size=len(atco_codes))

    # Fetch ID mappings from Bods DB
    atco_code_id_map = repo.get_ids_by_atco(atco_codes)

    if not atco_code_id_map:
        log.warning("No matching IDs found for batch", batch_size=len(atco_codes))
        return 0, 0

    if len(atco_code_id_map) != len(atco_codes):
        missing_stop_points = [
            atco_code for atco_code in atco_codes if atco_code not in atco_code_id_map
        ]
        log.warning(
            "Not all Stop Points were found in Bods DB",
            missing_stop_points=missing_stop_points,
        )

    log.info("Updating DynamoDB records", batch_size=len(atco_code_id_map))

    return await dynamo_loader.async_update_private_codes(atco_code_id_map)


async def process_private_code_updates(
    dynamo_loader: DynamoDBLoader, naptan_repo: NaptanStopPointRepo
) -> tuple[int, int]:
    """Process AtcoCodes in batches using async DynamoDB updates."""
    total_processed = 0
    total_errors = 0
    active_tasks: list[asyncio.Task[tuple[int, int]]] = []

    async def wait_for_slot() -> None:
        """Wait for a task slot to become available and process completed tasks."""
        nonlocal total_processed, total_errors, active_tasks

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
        async for atco_batch in dynamo_loader.stream_atco_codes(batch_size=BATCH_SIZE):
            if not atco_batch:
                continue

            # Wait for a slot if we're at max concurrency
            while len(active_tasks) >= dynamo_loader.max_concurrent_batches:
                await wait_for_slot()

            # Create new processing task
            task = asyncio.create_task(
                process_batch(atco_batch, dynamo_loader, naptan_repo)
            )
            active_tasks.append(task)

        # Process remaining tasks
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


@tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Lambda handler for updating Naptan Stop Points in DynamoDB with IDs from Postgres."""
    configure_logging(event, context)

    dynamo_loader = DynamoDBLoader(
        table_name="naptan-stop-points-table", max_concurrent_batches=100
    )
    db = SqlDB()
    naptan_repo = NaptanStopPointRepo(db)

    total_processed, total_errors = asyncio.run(
        process_private_code_updates(dynamo_loader, naptan_repo)
    )

    return {
        "statusCode": 200,
        "body": {
            "message": "Successfully updated NaPTAN StopPoint IDs",
            "processed_count": total_processed,
            "failed_count": total_errors,
        },
    }
