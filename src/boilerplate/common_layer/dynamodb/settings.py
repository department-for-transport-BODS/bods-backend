from enum import Enum

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DynamoDBConfig(BaseSettings):
    """
    Configuration for DynamoDB, loaded from env vars by default
    """

    DYNAMODB_ENDPOINT_URL: str = Field(
        default="http://host.docker.internal:4566",
        description="Endpoint URL for DynamoDB",
    )
    DYNAMODB_TABLE_NAME: str = Field(
        default="",
        description="Table Name for DynamoDB cache",
    )
    AWS_REGION: str = Field(
        default="eu-west-2",
        description="AWS Region for DynamoDB Table",
    )


class DynamoDBSettings(BaseModel):
