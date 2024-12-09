from gc import freeze
from unittest.mock import patch, MagicMock

from freezegun import freeze_time
import pytest
from common_layer.dynamodb.client import DynamoDB, TABLE_NAME
from common_layer.exceptions.pipeline_exceptions import PipelineException


def test_put():
    mock_client = MagicMock()
    mock_client.return_value.put_item = MagicMock()
    DynamoDB.client = mock_client

    with freeze_time("2024-12-06 12:00:00"):
        ttl = 3600
        expected_dynamo_ttl = 1733490000  # Epoch time for 2024-12-06 12:00:00 + 3600 seconds

        DynamoDB.put("test-key", {"key": "value"}, ttl=ttl)

        mock_client.return_value.put_item.assert_called_once_with(
            TableName=TABLE_NAME,
            Item={
                "Key": {"S": "test-key"},
                "Value": {"M": {"key": {"S": "value"}}},
                "ttl": expected_dynamo_ttl,
            },
        )

def test_put_exception():
    mock_client = MagicMock()
    mock_client.return_value.put_item.side_effect = Exception("Client exception")
    DynamoDB.client = mock_client
    with pytest.raises(PipelineException, match="Failed to set item with key 'test-key': Client exception"):
        DynamoDB.put("test-key", {"key": "value"}, ttl=3600)

def test_get():
    mock_client = MagicMock()
    mock_client.return_value.get_item = MagicMock(
        return_value={
            "Item": {"Key": {"S": "test-key"}, "Value": {"M": {"key": {"S": "value"}}}}
        }
    )
    DynamoDB.client = mock_client

    result = DynamoDB.get("test-key")

    mock_client.return_value.get_item.assert_called_once_with(
        TableName=TABLE_NAME, Key={"Key": {"S": "test-key"}}
    )
    assert result == {"key": "value"}

def test_get_exception():
    mock_client = MagicMock()
    mock_client.return_value.get_item.side_effect = Exception("Client exception")
    DynamoDB.client = mock_client
    with pytest.raises(PipelineException, match="Failed to get item with key 'test-key': Client exception"):
        DynamoDB.get("test-key")