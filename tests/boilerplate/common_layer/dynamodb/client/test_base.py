"""
Base DynamoDB Tests
"""

from unittest.mock import MagicMock

import pytest
from common_layer.dynamodb.client import DynamoDB, DynamoDBSettings
from common_layer.exceptions.pipeline_exceptions import PipelineException
from freezegun import freeze_time


def test_put(m_boto_client):
    """
    Test Putting into DynamoDB
    """
    settings = DynamoDBSettings()
    with freeze_time("2024-12-06 12:00:00"):
        ttl = 3600
        expected_dynamo_ttl = (
            1733490000  # Epoch time for 2024-12-06 12:00:00 + 3600 seconds
        )

        dynamo = DynamoDB()
        dynamo.put("test-key", {"key": "value"}, ttl=ttl)

        m_boto_client.put_item.assert_called_once_with(
            TableName=settings.DYNAMODB_TABLE_NAME,
            Item={
                "Key": {"S": "test-key"},
                "Value": {"M": {"key": {"S": "value"}}},
                "ttl": {"S": str(expected_dynamo_ttl)},
            },
        )


def test_put_exception(m_boto_client):
    """
    Test Put Raises Exception
    """
    m_boto_client.put_item.side_effect = Exception("Client exception")
    dynamodb = DynamoDB()
    with pytest.raises(
        PipelineException,
        match="Failed to set item with key 'test-key': Client exception",
    ):
        dynamodb.put("test-key", {"key": "value"}, ttl=3600)


def test_get(m_boto_client):
    """
    Test Getting data from MongoDB
    """
    settings = DynamoDBSettings()
    m_boto_client.get_item = MagicMock(
        return_value={
            "Item": {"Key": {"S": "test-key"}, "Value": {"M": {"key": {"S": "value"}}}}
        }
    )

    dynamodb = DynamoDB()
    result = dynamodb.get("test-key")

    m_boto_client.get_item.assert_called_once_with(
        TableName=settings.DYNAMODB_TABLE_NAME, Key={"Key": {"S": "test-key"}}
    )
    assert result == {"key": "value"}


def test_get_exception(m_boto_client):
    """
    Test Get Exception
    """
    m_boto_client.get_item.side_effect = Exception("Client exception")
    dynamodb = DynamoDB()
    with pytest.raises(
        PipelineException,
        match="Failed to get item with key 'test-key': Client exception",
    ):
        dynamodb.get("test-key")
