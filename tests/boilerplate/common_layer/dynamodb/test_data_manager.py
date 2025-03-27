"""
Test DynamoDB Data Manager
"""

from datetime import datetime
from types import MethodType
from unittest.mock import MagicMock, create_autospec, patch

from common_layer.database.client import SqlDB
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.dynamodb.models import TXCFileAttributes
from freezegun import freeze_time

from tests.factories.database.organisation import (
    OrganisationDatasetFactory,
    OrganisationDatasetRevisionFactory,
    OrganisationTXCFileAttributesFactory,
)


def test_prefetch_and_cache_data():
    """
    Test that all expected caching methods are called
    """
    draft_revision_id = 123
    draft_revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=draft_revision_id
    )

    data_manager = FileProcessingDataManager(
        db=MagicMock(spec=SqlDB), dynamodb=MagicMock(spec=DynamoDBCache)
    )

    # Mock internal caching functions
    data_manager._cache_live_txc_file_attributes = MethodType(
        create_autospec(FileProcessingDataManager._cache_live_txc_file_attributes),
        data_manager,
    )
    data_manager._cache_stop_activity_id_map = MethodType(
        create_autospec(FileProcessingDataManager._cache_stop_activity_id_map),
        data_manager,
    )

    data_manager.prefetch_and_cache_data(draft_revision)

    # Assert expected caching functions are called
    data_manager._cache_live_txc_file_attributes.assert_called_once()
    data_manager._cache_stop_activity_id_map.assert_called_once()


@patch("common_layer.dynamodb.data_manager.OrganisationTXCFileAttributesRepo")
@patch("common_layer.dynamodb.data_manager.OrganisationDatasetRepo")
def test_cache_live_txc_file_attributes(
    m_dataset_repo, m_file_attributes_repo, cached_attributes, frozen_time
):
    """
    Test prefetching and caching data
    """
    m_db = MagicMock(spec=SqlDB)
    m_dynamodb = MagicMock(spec=DynamoDBCache)

    draft_revision_id = 123
    draft_revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=draft_revision_id
    )
    expected_cache_key = "revision-123-live_txc_file_attributes"

    live_revision_id = 321
    live_revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=live_revision_id, dataset_id=draft_revision.dataset_id
    )

    m_dataset = OrganisationDatasetFactory.create_with_id(
        id_number=draft_revision.dataset_id, live_revision_id=live_revision.id
    )
    m_dataset_repo.return_value.get_by_id.return_value = m_dataset

    with freeze_time("2024-10-12 12:00:00"):
        now = datetime.now()
        live_attributes_1 = OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=1,
            revision_number=10,
            service_code="XYZ",
            line_names=["line1", "line2"],
            modification_datetime=now,
            hash="filehash1",
            filename="file1.xml",
        )
        live_attributes_2 = OrganisationTXCFileAttributesFactory.create_with_id(
            id_number=2,
            revision_number=10,
            service_code="ZYX",
            line_names=["line3", "line4"],
            modification_datetime=now,
            hash="filehash2",
            filename="file2.xml",
        )
        m_file_attributes_repo.return_value.get_by_revision_id.return_value = [
            live_attributes_1,
            live_attributes_2,
        ]

        data_manager = FileProcessingDataManager(db=m_db, dynamodb=m_dynamodb)
        data_manager._cache_live_txc_file_attributes(draft_revision)

    m_file_attributes_repo.return_value.get_by_revision_id.assert_called_with(
        live_revision_id
    )
    m_dynamodb.put.assert_called_once_with(
        expected_cache_key, cached_attributes, ttl=3600
    )


def test_get_cached_live_txc_file_attributes(cached_attributes):
    """
    Test getting live txc file attributes from cache
    """
    m_db = MagicMock(spec=SqlDB)
    m_dynamodb = MagicMock(spec=DynamoDBCache)

    m_dynamodb.get.return_value = cached_attributes

    revision_id = 123
    expected_cache_key = "revision-123-live_txc_file_attributes"

    data_manager = FileProcessingDataManager(db=m_db, dynamodb=m_dynamodb)
    result = data_manager.get_cached_live_txc_file_attributes(revision_id=revision_id)

    assert result == [
        TXCFileAttributes(**cached_attributes[0]),
        TXCFileAttributes(**cached_attributes[1]),
    ]
    m_dynamodb.get.assert_called_once_with(expected_cache_key)


def test_get_cached_live_txc_file_attributes_cache_miss():
    """
    Should return None on cache miss
    """
    m_db = MagicMock(spec=SqlDB)
    m_dynamodb = MagicMock(spec=DynamoDBCache)

    m_dynamodb.get.return_value = None

    revision_id = 123
    expected_cache_key = "revision-123-live_txc_file_attributes"

    data_manager = FileProcessingDataManager(db=m_db, dynamodb=m_dynamodb)
    result = data_manager.get_cached_live_txc_file_attributes(revision_id=revision_id)

    assert result is None
    m_dynamodb.get.assert_called_once_with(expected_cache_key)


@patch("common_layer.dynamodb.data_manager.TransmodelStopActivityRepo")
def test_get_or_compute_stop_activity_id_map(m_stop_activity_repo):

    m_db = create_autospec(SqlDB, instance=True)
    m_dynamodb = create_autospec(spec=DynamoDBCache, instance=True)
    data_manager = FileProcessingDataManager(db=m_db, dynamodb=m_dynamodb)

    expected_cache_key = "transmodel_stop_activity_id_map"
    m_stop_activity_repo.return_value.get_activity_id_map.return_value = {"pickUp": 1}

    data_manager.get_or_compute_stop_activity_id_map()

    args, kwargs = m_dynamodb.get_or_compute.call_args
    assert args[0] == expected_cache_key
    assert kwargs["ttl"] == 3600

    # Check correct compute function was passed
    actual_compute_fn = kwargs["compute_fn"]
    expected_result = m_stop_activity_repo.return_value.get_activity_id_map.return_value

    assert actual_compute_fn() == expected_result
