"""
Lambda handler for creating batches to be processed by the Consolidate Tracks lambda
"""

import json
from typing import Any
from uuid import uuid4

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database import SqlDB
from common_layer.database.repos import TransmodelTrackRepo
from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from pydantic import BaseModel, ValidationError
from structlog.stdlib import get_logger

tracer = Tracer()
log = get_logger()


class ConsolidateTracksBatcherInput(BaseModel):
    """Input schema for Consolidate Tracks Lambda."""

    batch_size: int = 500
    s3_bucket: str


def write_batches_to_s3(
    bucket_name: str, stop_point_batches: list[list[tuple[str, str]]]
) -> str:
    """
    Write batched stop point pairs to S3 to be used by MapRun
    """
    json_data = json.dumps(stop_point_batches).encode("utf-8")
    s3_key = f"consolidate-tracks-batch/{uuid4()}.json"
    s3_handler = S3(bucket_name=bucket_name)
    s3_handler.put_object(s3_key, json_data)
    return s3_key


@tracer.capture_lambda_handler
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, str]:
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
        "Uploading batched stoppoints to S3",
        number_of_batches=len(batches),
        batch_size=input_data.batch_size,
    )
    s3_key = write_batches_to_s3(input_data.s3_bucket, batches)

    return {
        "s3Key": s3_key,
    }
