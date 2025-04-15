"""
PTI Fixtures
"""

from io import BytesIO
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.response import StreamingBody


@pytest.fixture(autouse=True)
def mock_sqldb() -> Generator[MagicMock | AsyncMock, Any, None]:
    """
    Mock Database
    """
    with patch("common_layer.db.file_processing_result.SqlDB") as mock:
        mock_instance = MagicMock()
        mock.get_db.return_value = mock_instance
        yield mock


@pytest.fixture(name="s3_content")
def mocked_s3_content() -> bytes:
    """
    Mocked S3 Data
    """
    return b"<xml></xml>"


@pytest.fixture
def s3_file(s3_content: bytes) -> StreamingBody:
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
    context._aws_request_id = "test-123"  # type: ignore
    context._function_name = "test-function"  # type: ignore
    context._log_group_name = "/aws/lambda/test"  # type: ignore
    return context
