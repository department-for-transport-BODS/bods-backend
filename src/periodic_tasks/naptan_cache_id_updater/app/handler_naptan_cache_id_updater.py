"""
Lambda handler for updating the PrivateCodes in the 
Naptan StopPoints DynamoDB table with IDs from Bods DB.
"""

import asyncio
import json
from typing import Any, Dict

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.dynamodb.client_loader import DynamoDBLoader
from common_layer.json_logging import configure_logging
from pydantic import BaseModel, ValidationError, field_validator
from structlog.stdlib import get_logger

from .process_updates import process_private_code_updates

tracer = Tracer()
log = get_logger()


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
    """Lambda handler for updating Naptan Stop Points in DynamoDB with IDs from Bods DB."""
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
