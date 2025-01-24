from pydantic import Field
from pydantic_settings import BaseSettings


class DynamoBaseSettings(BaseSettings):
    """
    BaseSettings for DynamoDB client
    """

    DYNAMODB_ENDPOINT_URL: str = Field(
        default="http://host.docker.internal:4566",
        description="Endpoint URL for DynamoDB",
    )
    AWS_REGION: str = Field(
        default="eu-west-2",
        description="AWS Region for DynamoDB Table",
    )


class DynamoDBSettings(DynamoBaseSettings):
    """
    Settings for DynamoDB client
    """

    DYNAMODB_TABLE_NAME: str = Field(
        default="",
        description="Table Name for DynamoDB",
    )
