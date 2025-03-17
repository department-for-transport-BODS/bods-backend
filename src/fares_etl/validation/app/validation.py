"""
Fares Validation
"""

import os
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.dynamodb.client.fares_metadata import DynamoDBFaresMetadata
from common_layer.dynamodb.models import FaresViolation
from common_layer.s3 import S3
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

from .fares_validator import FaresValidator

logger = get_logger()


class FaresValidationInputData(BaseModel):
    """
    Input data for the Fares Validation Function
    """

    task_id: int = Field(alias="DatasetEtlTaskResultId")
    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")


def save_violations_to_dynamo(
    input_data: FaresValidationInputData, violations: list[FaresViolation]
):
    """
    Save fares violations to dynamo
    """
    dynamodb_fares_metadata_repo = DynamoDBFaresMetadata()

    dynamodb_fares_metadata_repo.put_violations(
        input_data.task_id, os.path.basename(input_data.s3_file_key), violations
    )


def get_file_from_s3_and_validate(input_data: FaresValidationInputData):
    """
    Retrieve NeTEx file from S3 and validate it against the schema
    """
    s3_client = S3(input_data.s3_bucket_name)
    file = s3_client.get_object(input_data.s3_file_key)

    validator = FaresValidator()

    return validator.get_violations(file)


@file_processing_result_to_db(step_name=StepName.NETEX_FILE_VALIDATOR)
def lambda_handler(
    event: dict[str, Any], _context: LambdaContext
) -> dict[str, str | int]:
    """
    Lambda handler for file validation
    """
    input_data = FaresValidationInputData(**event)
    violations = get_file_from_s3_and_validate(input_data)

    if len(violations) > 0:
        logger.info(
            f"File {input_data.s3_file_key} in bucket {input_data.s3_bucket_name} \
has {len(violations)} violations"
        )

        save_violations_to_dynamo(input_data, violations)

    return {
        "statusCode": 200,
        "body": f"Completed Fares File Validation, found {len(violations)} violations",
    }
