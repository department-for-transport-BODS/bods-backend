from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import DynamoDB
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.dynamodb.models import TXCFileAttributes
from freezegun import freeze_time

from tests.factories.database.organisation import (
    OrganisationDatasetRevisionFactory,
    OrganisationTXCFileAttributesFactory,
)


@pytest.fixture
def frozen_time():
    """Set a consistent datetime for tests."""
    with freeze_time("2024-10-12 12:00:00"):
        yield datetime.now()


@pytest.fixture
def cached_attributes(frozen_time):
    timestamp = int(frozen_time.timestamp())
    return [
        {
            "id": 1,
            "revision_number": 10,
            "service_code": "XYZ",
            "line_names": ["line1", "line2"],
            "modification_datetime": timestamp,
            "hash": "filehash1",
            "filename": "file1.xml",
        },
        {
            "id": 2,
            "revision_number": 10,
            "service_code": "ZYX",
            "line_names": ["line3", "line4"],
            "modification_datetime": timestamp,
            "hash": "filehash2",
            "filename": "file2.xml",
        },
    ]


@patch("common_layer.dynamodb.data_manager.OrganisationTXCFileAttributesRepo")
@patch("common_layer.dynamodb.data_manager.OrganisationDatasetRepo")
def test_prefetch_and_cache_data(
    m_dataset_repo, m_file_attributes_repo, cached_attributes, frozen_time
):
    m_db = MagicMock(spec=SqlDB)
    m_dynamodb = MagicMock(spec=DynamoDB)

    draft_revision_id = 123
    draft_revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=draft_revision_id
    )
    expected_cache_key = "revision-123-live_txc_file_attributes"

    live_revision_id = 321
    live_revision = OrganisationDatasetRevisionFactory.create_with_id(
        id_number=live_revision_id, dataset_id=draft_revision.dataset_id
    )

    # TODO: Add DatasetFactory
    m_dataset = MagicMock(
        id=draft_revision.dataset_id, live_revision_id=live_revision.id
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
        data_manager.prefetch_and_cache_data(draft_revision)

    m_file_attributes_repo.return_value.get_by_revision_id.assert_called_with(
        live_revision_id
    )
    m_dynamodb.put.assert_called_once_with(
        expected_cache_key, cached_attributes, ttl=3600
    )


def test_get_cached_live_txc_file_attributes(cached_attributes):
    m_db = MagicMock(spec=SqlDB)
    m_dynamodb = MagicMock(spec=DynamoDB)

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
    m_dynamodb = MagicMock(spec=DynamoDB)

    m_dynamodb.get.return_value = None

    revision_id = 123
    expected_cache_key = "revision-123-live_txc_file_attributes"

    data_manager = FileProcessingDataManager(db=m_db, dynamodb=m_dynamodb)
    result = data_manager.get_cached_live_txc_file_attributes(revision_id=revision_id)

    assert result is None
    m_dynamodb.get.assert_called_once_with(expected_cache_key)
