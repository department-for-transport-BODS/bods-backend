"""
DynamoDB cache tests
"""

from unittest.mock import MagicMock

from common_layer.dynamodb.client import DynamoDBCache
from freezegun import freeze_time


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


def test_get_or_compute_refreshes_expired_legacy_entry(m_boto_client):
    m_boto_client.get_item.return_value = {
        "Item": {
            "Key": {"S": "transmodel_stop_activity_id_map"},
            "Value": {"M": {"pickUp": {"N": "1"}}},
            "ttl": {"S": "1733486399"},
        }
    }
    compute = MagicMock(return_value={"pickUp": 1, "noPickUpAndSetDown": 9})

    with freeze_time("2024-12-06 12:00:00"):
        result = DynamoDBCache().get_or_compute(
            "transmodel_stop_activity_id_map", compute, ttl=3600
        )

    assert result == {"pickUp": 1, "noPickUpAndSetDown": 9}
    compute.assert_called_once_with()
    assert m_boto_client.put_item.call_args.kwargs["Item"] == {
        "Key": {"S": "transmodel_stop_activity_id_map"},
        "Value": {"M": {"pickUp": {"N": "1"}, "noPickUpAndSetDown": {"N": "9"}}},
        "ttl": {"N": "1733490000"},
    }
