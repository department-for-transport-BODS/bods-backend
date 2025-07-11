"""
Test PTI Validation Handler
"""

from typing import Generator, Protocol
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.response import StreamingBody
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.xml.txc.models.txc_data import TXCData
from pti.app.pti_validation import lambda_handler

from tests.factories.database.organisation import (
    OrganisationDatasetRevisionFactory,
    OrganisationTXCFileAttributesFactory,
)

TEST_ENV_VAR = {
    "PROJECT_ENV": "dev",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_pass",
    "POSTGRES_DB": "test_db",
}


class MockImports(Protocol):
    """
    Group up the Mock Imports
    """

    S3: MagicMock
    DynamoDBCache: MagicMock
    NaptanStopPointDynamoDBClient: MagicMock
    FileProcessingDataManager: MagicMock
    OrganisationDatasetRevisionRepo: MagicMock
    OrganisationTXCFileAttributesRepo: MagicMock
    PTIValidationService: MagicMock
    file_processing: MagicMock
    parse_txc_file: MagicMock
    send_email: MagicMock


@pytest.fixture(autouse=True)
def mock_imports() -> Generator[MockImports, None, None]:
    """
    Mock imports for testing.

    While this approach works, a cleaner approach would be to use individual fixtures
    for each dependency that needs to be mocked rather than a single large fixture.

    Returns:
        A generator that yields a mock object with all required dependencies
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
        "send_email": patch("pti.app.pti_validation.send_email"),
    }

    mocks: dict[str, MagicMock | AsyncMock] = {}
    for name, patcher in patches.items():
        mock = patcher.start()
        if name == "file_processing":
            mock.side_effect = lambda step_name: lambda func: func  # type: ignore
        mocks[name] = mock

    # Create the mock object with proper typing
    result = type("Mocks", (), mocks)

    # Type assertion to satisfy the type checker
    yield result  # type: ignore

    for patcher in patches.values():
        patcher.stop()


@pytest.mark.parametrize(
    "has_file_attributes, expected_status",
    [
        (True, 200),
    ],
    ids=["Success case"],
)
@patch.dict("os.environ", TEST_ENV_VAR)
def test_lambda_handler_success(
    mock_imports: MockImports,
    mock_sqldb: MagicMock | AsyncMock,
    s3_file: StreamingBody,
    s3_content: bytes,
    has_file_attributes: bool,
    expected_status: int,
    lambda_context: LambdaContext,
) -> None:
    """
    Test Lambda Handler for PTI Validation - Success Path

    Args:
        mock_imports: Fixture containing all mocked dependencies
        mock_sqldb: Mock SQL database connection
        s3_file: Mock S3 file object
        s3_content: Mock S3 file content
        has_file_attributes: Whether the file has attributes
        expected_status: Expected HTTP status code
        lambda_context: AWS Lambda context
    """
    event: dict[str, str | int] = {
        "Bucket": "test-bucket",
        "ObjectKey": "test-key",
        "DatasetRevisionId": 123,
        "TxcFileAttributesId": 123,
    }
    txc_data = TXCData.model_construct()

    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=123)
    mock_imports.OrganisationDatasetRevisionRepo.return_value.require_by_id.return_value = (
        revision
    )

    file_attrs = OrganisationTXCFileAttributesFactory.create()
    mock_imports.OrganisationTXCFileAttributesRepo.return_value.require_by_id.return_value = (
        file_attrs
    )
    expected_attrs = TXCFileAttributes.from_orm(file_attrs)

    mock_imports.S3.return_value.get_object.return_value = s3_file
    mock_imports.parse_txc_file.return_value = txc_data
    mock_imports.send_email.return_value = True

    result = lambda_handler(event, lambda_context)
    assert result == {"statusCode": expected_status}

    validate_call = mock_imports.PTIValidationService.return_value.validate.call_args[0]
    assert validate_call[0] == revision
    assert validate_call[1].read() == s3_content
    assert validate_call[2] == expected_attrs
    assert validate_call[3] == txc_data


@pytest.mark.parametrize(
    "has_file_attributes",
    [
        (False),
    ],
    ids=["No valid files"],
)
@patch.dict("os.environ", TEST_ENV_VAR)
def test_lambda_handler_error(
    mock_imports: MockImports,
    mock_sqldb: MagicMock | AsyncMock,
    s3_file: StreamingBody,
    s3_content: bytes,
    has_file_attributes: bool,
    lambda_context: LambdaContext,
) -> None:
    """
    Test Lambda Handler for PTI Validation - Error Path

    Args:
        mock_imports: Fixture containing all mocked dependencies
        mock_sqldb: Mock SQL database connection
        s3_file: Mock S3 file object
        s3_content: Mock S3 file content
        has_file_attributes: Whether the file has attributes
        lambda_context: AWS Lambda context
    """
    event: dict[str, str | int] = {
        "Bucket": "test-bucket",
        "ObjectKey": "test-key",
        "DatasetRevisionId": 123,
        "TxcFileAttributesId": 123,
    }
    txc_data = TXCData.model_construct()

    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=123)
    mock_imports.OrganisationDatasetRevisionRepo.return_value.require_by_id.return_value = (
        revision
    )

    mock_imports.OrganisationTXCFileAttributesRepo.return_value.require_by_id.side_effect = PipelineException(
        "Record not found"
    )

    mock_imports.S3.return_value.get_object.return_value = s3_file
    mock_imports.parse_txc_file.return_value = txc_data
    mock_imports.send_email.return_value = True

    with pytest.raises(PipelineException):
        lambda_handler(event, lambda_context)
