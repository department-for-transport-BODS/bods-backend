import asyncio
import json
import time
from typing import Any, Dict

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.dynamodb.client_loader import DynamoDBLoader
from common_layer.json_logging import configure_logging
from pydantic import BaseModel, ValidationError, field_validator
from structlog.stdlib import get_logger

tracer = Tracer()
log = get_logger()

BATCH_SIZE = 10000  # Adjust if necessary for performance tuning


async def process_batch(
    atco_code_id_map: dict[str, int],
    dynamo_loader: DynamoDBLoader,
    repo: NaptanStopPointRepo,
) -> tuple[int, int]:
    """Fetch corresponding IDs from Postgres and update in DynamoDB."""
    if not atco_code_id_map:
        log.warning("atco_code_id_map empty")
        return 0, 0
    log.info("Updating DynamoDB records", batch_size=len(atco_code_id_map))
    return await dynamo_loader.async_update_private_codes(atco_code_id_map)


async def process_private_code_updates(
    dynamo_loader: DynamoDBLoader, naptan_repo: NaptanStopPointRepo
) -> tuple[int, int]:
    """Process AtcoCodes in batches using async DynamoDB updates with controlled concurrency."""
    total_processed = 0
    total_errors = 0
    active_tasks: list[asyncio.Task[tuple[int, int]]] = []
    last_log_time = time.time()

    async def wait_for_slot() -> None:
        """Wait for a task slot to become available and process completed tasks."""
        nonlocal total_processed, total_errors, active_tasks, last_log_time

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
        async for atco_batch in naptan_repo.stream_naptan_ids(batch_size=BATCH_SIZE):
            log.info("Processing atco batch from Bods DB", batch_size=len(atco_batch))
            if not atco_batch:
                continue

            # Ensure we do not exceed max_concurrent_batches
            while len(active_tasks) >= dynamo_loader.max_concurrent_batches:
                await wait_for_slot()

            task = asyncio.create_task(
                process_batch(atco_batch, dynamo_loader, naptan_repo)
            )
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


class NaptanProcessingInput(BaseModel):
    """Input schema for NaPTAN processing Lambda."""

    dynamo_table: str
    aws_region: str = "eu-west-2"

    @field_validator("dynamo_table")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        """
        Ensure that there is a table name
        """
        if not v.strip():
            raise ValueError("DynamoDB table name cannot be empty")
        return v


@tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Lambda handler for updating Naptan Stop Points in DynamoDB with IDs from Postgres."""
    configure_logging(event, context)

    try:
        input_data = NaptanProcessingInput.model_validate(event)
    except ValidationError as e:
        log.error("Invalid input data", error=str(e))
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid input data", "errors": e.errors()}),
        }

    dynamo_loader = DynamoDBLoader(
        table_name=input_data.dynamo_table,
        region=input_data.aws_region,
        partition_key="AtcoCode",
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
