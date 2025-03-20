"""
Pydantic Models
"""

from enum import Enum

from pydantic import BaseModel, HttpUrl, field_validator


class WriteMode(str, Enum):
    """Enum for DynamoDB write modes."""

    BATCH = "batch"
    TRANSACT = "transact"


class NaptanProcessingInput(BaseModel):
    """Input schema for NaPTAN processing Lambda."""

    naptan_url: HttpUrl
    dynamo_table: str
    aws_region: str = "eu-west-2"
    max_concurrent_batches: int | None = None
    write_mode: WriteMode = WriteMode.BATCH

    @field_validator("dynamo_table")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        """
        Ensure that there is a table name
        """
        if not v.strip():
            raise ValueError("DynamoDB table name cannot be empty")
        return v
