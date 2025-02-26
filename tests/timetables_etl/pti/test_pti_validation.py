"""
Test PTI Validation Handler
"""

from unittest.mock import patch

import pytest
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


@pytest.mark.parametrize(
    "test_params",
    [
        pytest.param(
            {
                "has_file_attributes": True,
                "expected_status": 200,
                "should_raise": False,
            },
            id="success_case",
        ),
        pytest.param(
            {"has_file_attributes": False, "should_raise": True}, id="no_valid_files"
        ),
    ],
)
@patch.dict("os.environ", TEST_ENV_VAR)
def test_lambda_handler(
    mock_imports, mock_sqldb, s3_file, s3_content, test_params, lambda_context
):
    """
    Test Lambda Handler for PTI Validation
    """
    event = {
        "Bucket": "test-bucket",
        "ObjectKey": "test-key",
        "DatasetRevisionId": 123,
        "TxcFileAttributesId": 123,
    }
    txc_data = TXCData.model_construct()

    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=123)
    mock_imports.OrganisationDatasetRevisionRepo.return_value.get_by_id.return_value = (
        revision
    )

    if test_params["has_file_attributes"]:
        file_attrs = OrganisationTXCFileAttributesFactory.create()
        mock_imports.OrganisationTXCFileAttributesRepo.return_value.get_by_id.return_value = (
            file_attrs
        )
        expected_attrs = TXCFileAttributes.from_orm(file_attrs)
    else:
        mock_imports.OrganisationTXCFileAttributesRepo.return_value.get_by_id.return_value = (
            None
        )
        expected_attrs = None

    mock_imports.S3.return_value.get_object.return_value = s3_file
    mock_imports.parse_txc_file.return_value = txc_data

    if test_params["should_raise"]:
        with pytest.raises(PipelineException):
            lambda_handler(event, lambda_context)
    else:
        result = lambda_handler(event, lambda_context)
        assert result == {"statusCode": test_params["expected_status"]}

        validate_call = (
            mock_imports.PTIValidationService.return_value.validate.call_args[0]
        )
        assert validate_call[0] == revision
        assert validate_call[1].read() == s3_content
        assert validate_call[2] == expected_attrs
        assert validate_call[3] == txc_data
