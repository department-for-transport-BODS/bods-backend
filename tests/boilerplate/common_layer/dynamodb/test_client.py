from gc import freeze
from unittest.mock import patch, MagicMock

from freezegun import freeze_time
import pytest
from common_layer.dynamodb.client import DynamoDB, TABLE_NAME
from common_layer.exceptions.pipeline_exceptions import PipelineException

@pytest.fixture
def m_boto_client():
    with patch("common_layer.dynamodb.client.boto3.client") as m_boto:
        yield m_boto.return_value


def test_put(m_boto_client):
    with freeze_time("2024-12-06 12:00:00"):
        ttl = 3600
        expected_dynamo_ttl = 1733490000  # Epoch time for 2024-12-06 12:00:00 + 3600 seconds

        dynamo = DynamoDB()
        dynamo.put("test-key", {"key": "value"}, ttl=ttl)

        m_boto_client.put_item.assert_called_once_with(
            TableName=TABLE_NAME,
            Item={
                "Key": {"S": "test-key"},
                "Value": {"M": {"key": {"S": "value"}}},
                "ttl": expected_dynamo_ttl,
            },
        )

def test_put_exception(m_boto_client):
    m_boto_client.put_item.side_effect = Exception("Client exception")
    dynamodb = DynamoDB()
    with pytest.raises(PipelineException, match="Failed to set item with key 'test-key': Client exception"):
        dynamodb.put("test-key", {"key": "value"}, ttl=3600)

def test_get(m_boto_client):
    m_boto_client.get_item = MagicMock(
        return_value={
            "Item": {"Key": {"S": "test-key"}, "Value": {"M": {"key": {"S": "value"}}}}
        }
    )

    dynamodb = DynamoDB()
    result = dynamodb.get("test-key")

    m_boto_client.get_item.assert_called_once_with(
        TableName=TABLE_NAME, Key={"Key": {"S": "test-key"}}
    )
    assert result == {"key": "value"}

def test_get_exception(m_boto_client):
    m_boto_client.get_item.side_effect = Exception("Client exception")
    dynamodb = DynamoDB()
    with pytest.raises(PipelineException, match="Failed to get item with key 'test-key': Client exception"):
        dynamodb.get("test-key")