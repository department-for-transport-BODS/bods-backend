"""
PTI Fixtures
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from botocore.response import StreamingBody


@pytest.fixture(autouse=True)
def mock_sqldb():
    """
    Mock Database
    """
    with patch("common_layer.db.file_processing_result.SqlDB") as mock:
        mock_instance = MagicMock()
        mock.get_db.return_value = mock_instance
        yield mock


@pytest.fixture(autouse=True)
def mock_imports():
    """
    Mock Imports
    """
    patches = {
        "S3": patch("pti.app.pti_validation.S3"),
        "DynamoDBCache": patch("pti.app.pti_validation.DynamoDBCache"),
        "NaptanStopPointDynamoDBClient": patch(
            "pti.app.pti_validation.NaptanStopPointDynamoDBClient"
        ),
        "FileProcessingDataManager": patch(
            "pti.app.pti_validation.FileProcessingDataManager"
        ),
        "OrganisationDatasetRevisionRepo": patch(
            "pti.app.pti_validation.OrganisationDatasetRevisionRepo"
        ),
        "OrganisationTXCFileAttributesRepo": patch(
            "pti.app.pti_validation.OrganisationTXCFileAttributesRepo"
        ),
        "PTIValidationService": patch("pti.app.pti_validation.PTIValidationService"),
        "file_processing": patch(
            "common_layer.db.file_processing_result.file_processing_result_to_db"
        ),
        "parse_txc_file": patch("pti.app.pti_validation.parse_txc_from_element"),
    }

    mocks = {}
    for name, patcher in patches.items():
        mock = patcher.start()
        if name == "file_processing":
            mock.side_effect = lambda step_name: lambda func: func
        mocks[name] = mock

    yield type("Mocks", (), mocks)

    for patcher in patches.values():
        patcher.stop()


@pytest.fixture(name="s3_content")
def mocked_s3_content():
    """
    Mocked S3 Data
    """
    return b"<xml></xml>"


@pytest.fixture
def s3_file(s3_content):
    """
    Mocked S3 File
    """
    stream = StreamingBody(BytesIO(s3_content), len(s3_content))
    return stream
