"""
PTI Fixtures
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
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


# pylint: disable=protected-access
@pytest.fixture(name="lambda_context")
def lambda_context_fixture() -> LambdaContext:
    """
    Lambda Context
    """
    context = LambdaContext()
    context._aws_request_id = "test-123"
    context._function_name = "test-function"
    context._log_group_name = "/aws/lambda/test"
    return context
