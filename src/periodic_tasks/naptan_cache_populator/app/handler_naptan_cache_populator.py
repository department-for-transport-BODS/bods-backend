"""
Naptan Cache Lambda
"""

import json
from pathlib import Path
from typing import Any

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.dynamodb.client_loader import DynamoDBLoader
from common_layer.json_logging import configure_logging
from pydantic import ValidationError
from structlog.stdlib import get_logger

from .data_loader.naptan_parser_xml import load_naptan_data_from_xml
from .naptan_cache_models import NaptanProcessingInput

tracer = Tracer()
log = get_logger()


@tracer.capture_lambda_handler
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for loading Naptan Data in to DynamoDB
    """
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
        max_concurrent_batches=input_data.max_concurrent_batches,
    )

    processed_count, error_count = load_naptan_data_from_xml(
        url=str(input_data.naptan_url),
        data_dir=Path("/tmp"),
        dynamo_loader=dynamo_loader,
        write_mode=input_data.write_mode,
    )

    response = {
        "statusCode": 200,
        "body": {
            "message": "Successfully processed NaPTAN data",
            "processed_count": processed_count,
            "error_count": error_count,
            "table": input_data.dynamo_table,
            "region": input_data.aws_region,
        },
    }

    log.info(
        "Successfully completed NaPTAN processing",
        processed_count=processed_count,
        error_count=error_count,
        table=input_data.dynamo_table,
    )

    return response
