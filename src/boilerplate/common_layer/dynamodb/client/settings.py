"""
Base Settings Models for DynamoDB client
"""

from common_layer.database.client import ProjectEnvironment
from pydantic import Field
from pydantic_settings import BaseSettings


class DynamoBaseSettings(BaseSettings):
    """
    BaseSettings for DynamoDB client
    """

    PROJECT_ENV: ProjectEnvironment = Field(
        default=ProjectEnvironment.LOCAL, description="Project environment"
    )
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


class NaptanDynamoDBSettings(DynamoBaseSettings):
    """
    Settings for DynamoDBCache client
    """

    DYNAMODB_NAPTAN_STOP_POINT_TABLE_NAME: str = Field(
        default="",
        description="Table Name for NAPTAN StopPoint table",
    )
