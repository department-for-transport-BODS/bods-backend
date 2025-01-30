"""
DynamoDB Cache Client
"""

from typing import Any, Callable

from pydantic import Field
from structlog.stdlib import get_logger

from .base import DynamoDB
from .settings import DynamoBaseSettings, DynamoDBSettings

log = get_logger()


class DynamoDbCacheSettings(DynamoBaseSettings):
    """
    Settings for DynamoDBCache client
    """

    DYNAMODB_CACHE_TABLE_NAME: str = Field(
        default="",
        description="Table Name for DynamoDB cache table",
    )


class DynamoDBCache(DynamoDB):
    """
    Client for interacting with DynamoDB cache table
    """

    def __init__(self, settings: DynamoDbCacheSettings | None = None):
        cache_settings = settings if settings else DynamoDbCacheSettings()
        super().__init__(
            DynamoDBSettings(
                DYNAMODB_ENDPOINT_URL=cache_settings.DYNAMODB_ENDPOINT_URL,
                AWS_REGION=cache_settings.AWS_REGION,
                DYNAMODB_TABLE_NAME=cache_settings.DYNAMODB_CACHE_TABLE_NAME,
                PROJECT_ENV=cache_settings.PROJECT_ENV,
            )
        )

    def get_or_compute(
        self, key: str, compute_fn: Callable[[], Any], ttl: int | None = None
    ) -> Any:
        """
        Get a value from cache or compute it and cache it if not found.
        """
        cached_value = self.get(key)

        if cached_value is not None:
            log.info("DynamoDB: Cache hit", key=key)
            return cached_value

        log.info("DynamoDB: Cache miss, computing value", key=key)
        computed_value = compute_fn()

        self.put(key, computed_value, ttl=ttl)

        return computed_value
