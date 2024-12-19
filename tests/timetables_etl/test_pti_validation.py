from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from botocore.response import StreamingBody
from common_layer.db.constants import StepName
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.exceptions.pipeline_exceptions import PipelineException

from tests.conftest import decorator_mock
from tests.timetables_etl.factories.database.organisation import (
    OrganisationDatasetRevisionFactory,
    OrganisationTXCFileAttributesFactory,
)

# Patch the file processing decorator before importing the module
with patch(
    "common_layer.db.file_processing_result.file_processing_result_to_db"
) as m_file_processing_result_to_db:

    def decorator_mock(step_name):
        def wrapper(func):
            return func

        return wrapper

    m_file_processing_result_to_db.side_effect = decorator_mock

    import pti_validation


@pytest.fixture(autouse=True, scope="module")
def m_db_manager():
    with patch("pti_validation.SqlDB") as m_db:
        yield m_db


@patch("pti_validation.FileProcessingDataManager")
@patch("pti_validation.DynamoDB")
@patch("pti_validation.OrganisationDatasetRevisionRepo")
@patch("pti_validation.S3")
@patch("pti_validation.OrganisationTXCFileAttributesRepo")
@patch("pti_validation.PTIValidationService")
def test_lambda_hander(
    m_pti_validation_service,
    m_file_attribute_repo,
    m_s3,
    m_revision_repo,
    m_dynamodb,
    m_data_manager,
):
    revision_id = 123
    event = {
        "Bucket": "test-bucket",
        "ObjectKey": "test-key",
        "DatasetRevisionId": revision_id,
    }

    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=revision_id)
    m_revision_repo.return_value.get_by_id.return_value = revision

    s3_file_obj = MagicMock()
    s3_file_obj = StreamingBody(BytesIO(b"<xml-content>"), len(b"<xml-content>"))
    m_s3.return_value.get_object.return_value = s3_file_obj

    txc_file_attributes = OrganisationTXCFileAttributesFactory.create()
    m_file_attribute_repo.return_value.get_by_revision_id_and_filename.return_value = (
        txc_file_attributes
    )
    expected_file_attributes = TXCFileAttributes.from_orm(txc_file_attributes)

    result = pti_validation.lambda_handler(event, {})

    assert result == {"statusCode": 200}
    m_s3.return_value.get_object.assert_called_once_with(file_path="test-key")
    m_pti_validation_service.return_value.validate.assert_called_once_with(
        revision, s3_file_obj, expected_file_attributes
    )
    m_file_processing_result_to_db.assert_called_once_with(
        step_name=StepName.PTI_VALIDATION
    )


@patch("pti_validation.FileProcessingDataManager")
@patch("pti_validation.DynamoDB")
@patch("pti_validation.OrganisationDatasetRevisionRepo")
@patch("pti_validation.S3")
@patch("pti_validation.OrganisationTXCFileAttributesRepo")
@patch("pti_validation.PTIValidationService")
def test_lambda_hander_no_valid_files(
    m_pti_validation_service,
    m_file_attribute_repo,
    m_s3,
    m_revision_repo,
    m_dynamodb,
    m_data_manager,
):

    revision_id = 123
    event = {
        "Bucket": "test-bucket",
        "ObjectKey": "test-key",
        "DatasetRevisionId": revision_id,
    }
    m_file_attribute_repo.return_value.get_by_revision_id_and_filename.return_value = (
        None
    )

    with pytest.raises(PipelineException):
        pti_validation.lambda_handler(event, {})

    m_file_processing_result_to_db.assert_called_once_with(
        step_name=StepName.PTI_VALIDATION
    )
