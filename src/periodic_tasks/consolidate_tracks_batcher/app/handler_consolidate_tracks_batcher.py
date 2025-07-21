"""
Lambda handler for creating batches to be processed by the Consolidate Tracks lambda
"""

from typing import Any

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database import SqlDB
from common_layer.database.repos import TransmodelTrackRepo
from common_layer.json_logging import configure_logging
from pydantic import BaseModel, ValidationError
from structlog.stdlib import get_logger

tracer = Tracer()
log = get_logger()


class ConsolidateTracksBatcherInput(BaseModel):
    """Input schema for Consolidate Tracks Lambda."""

    batch_size: int = 500


@tracer.capture_lambda_handler
def lambda_handler(
    event: dict[str, Any], context: LambdaContext
) -> list[list[tuple[str, str]]]:
    """
    Lambda handler for batching distinct stop point pairs
    to be processed by the Consolidate Tracks lambda.
    """
    configure_logging(event, context)

    try:
        input_data = ConsolidateTracksBatcherInput.model_validate(event)
    except ValidationError as e:
        log.error("Invalid input data", error=str(e))
        raise

    db = SqlDB()
    track_repo = TransmodelTrackRepo(db)

    log.info("Getting distinct stop point pairs with multiple track rows")
    all_stop_points = track_repo.get_distinct_stop_points_with_multiple_rows()

    batches = [
        all_stop_points[i : i + input_data.batch_size]
        for i in range(0, len(all_stop_points), input_data.batch_size)
    ]

    log.info(
        "Returning batched stop points",
        number_of_batches=len(batches),
        batch_size=input_data.batch_size,
    )

    return batches
