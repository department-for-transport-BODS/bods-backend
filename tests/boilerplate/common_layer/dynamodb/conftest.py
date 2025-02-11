"""
DynamoDB Client Fixtures
"""

from datetime import datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time


@pytest.fixture()
def m_boto_client():
    """
    Mocked Boto3 Client
    """
    with patch("common_layer.dynamodb.client.base.boto3.client") as m_boto:
        yield m_boto.return_value


@pytest.fixture
def frozen_time():
    """Set a consistent datetime for tests."""
    with freeze_time("2024-10-12 12:00:00"):
        yield datetime.now()


@pytest.fixture
def cached_attributes(frozen_time):
    """
    Return a set of cached Attributes
    """
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
