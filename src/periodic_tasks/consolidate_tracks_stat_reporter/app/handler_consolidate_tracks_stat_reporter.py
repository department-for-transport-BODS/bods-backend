"""
Lambda handler for aggregating and reporting stats returned by Consolidate Tracks map run
"""

import json
from collections import Counter
from typing import Any

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.aws.step import get_map_processing_results
from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from structlog.stdlib import get_logger

tracer = Tracer()
log = get_logger()


class ConsolidateTracksStatReporterInput(BaseModel):
    """Input schema for Consolidate Tracks Lambda."""

    model_config = ConfigDict(populate_by_name=True)

    map_run_arn: str = Field(alias="MapRunArn")
    map_run_prefix: str = Field(alias="MapRunPrefix")
    s3_bucket_name: str = Field(alias="Bucket")


@tracer.capture_lambda_handler
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, int]:
    """
    Lambda handler for batching distinct stop point pairs
    to be processed by the Consolidate Tracks lambda.
    """
    configure_logging(event, context)

    try:
        input_data = ConsolidateTracksStatReporterInput.model_validate(event)
    except ValidationError as e:
        log.error("Invalid input data", error=str(e))
        raise

    s3 = S3(input_data.s3_bucket_name)
    map_results = get_map_processing_results(
        s3, input_data.map_run_arn, input_data.map_run_prefix
    )

    stats_counter = Counter[str]()
    for result in map_results.succeeded:
        try:
            output_dict = json.loads(result.Output)
            stats = output_dict.get("stats", {})
            stats_counter.update(stats)
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.warning(
                "Failed to parse result output", error=str(e), output=result.Output
            )

    stats_counter.update({"failures": len(map_results.failed)})

    log.info("Aggregated Stats", **stats_counter)

    return stats_counter
