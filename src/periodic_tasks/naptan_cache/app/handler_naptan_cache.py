"""
Naptan Cache Lambda
"""

import json
import traceback
from pathlib import Path
from typing import Any

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.dynamodb.client_loader import DynamoDBLoader
from common_layer.json_logging import configure_logging
from pydantic import BaseModel, HttpUrl, ValidationError, field_validator
from structlog.stdlib import get_logger

from .data_loader.naptan_parser_xml import load_naptan_data_from_xml

tracer = Tracer()
log = get_logger()


class NaptanProcessingInput(BaseModel):
    """Input schema for NaPTAN processing Lambda."""

    naptan_url: HttpUrl
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
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for loading Naptan Data in to DynamoDB
    """
    configure_logging(context)
    try:
        try:
            input_data = NaptanProcessingInput.model_validate(event)
        except ValidationError as e:
            log.error("Invalid input data", error=str(e))
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": "Invalid input data", "errors": e.errors()}
                ),
            }

        dynamo_loader = DynamoDBLoader(
            table_name=input_data.dynamo_table, region=input_data.aws_region
        )

        processed_count, error_count = load_naptan_data_from_xml(
            url=str(input_data.naptan_url),
            data_dir=Path("/tmp"),
            dynamo_loader=dynamo_loader,
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

    except Exception as e:
        log.exception("Failed to process NaPTAN data")
        error_details = {
            "error": "DataProcessingError",
            "cause": str(e),
            "errorType": type(e).__name__,
            "stackTrace": [
                line
                for line in traceback.format_exc().split("\n")
                if line.strip() and 'File "<' not in line
            ][:10],
        }
        return {
            "statusCode": 500,
            "error": error_details,
        }
