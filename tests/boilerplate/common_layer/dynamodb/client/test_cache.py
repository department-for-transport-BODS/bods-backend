"""
DynamoDB cache tests
"""

from unittest.mock import MagicMock

from common_layer.dynamodb.client import DynamoDBCache


def test_get_or_compute_cache_hit(m_boto_client):
    """
    Test Getting or Computing data for DynamodB Cache Table
    """
    m_boto_client.get_item = MagicMock(
        return_value={
            "Item": {"Key": {"S": "test-key"}, "Value": {"M": {"key": {"S": "value"}}}}
        }
    )

    func_to_cache = MagicMock()

    dynamodb = DynamoDBCache()
    result = dynamodb.get_or_compute(
        key="test-key", compute_fn=lambda: func_to_cache(), ttl=7200
    )

    assert result == {"key": "value"}
    func_to_cache.assert_not_called()
    m_boto_client.put.assert_not_called()


def test_get_or_compute_cache_miss(m_boto_client):
    """
    Test DynamoDB Cache Misses
    """
    m_boto_client.get_item.return_value = {}

    func_to_cache = MagicMock(return_value={"key": "computed-value"})

    dynamodb = DynamoDBCache()
    dynamodb.put = MagicMock()

    result = dynamodb.get_or_compute(
        key="test-key", compute_fn=lambda: func_to_cache(), ttl=7200
    )

    assert result == {"key": "computed-value"}
    func_to_cache.assert_called_once()
    dynamodb.put.assert_called_once_with(
        "test-key", {"key": "computed-value"}, ttl=7200
    )
