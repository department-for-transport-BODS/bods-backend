from unittest.mock import MagicMock, patch

import pytest
from db.constants import StepName
from exceptions.pipeline_exceptions import PipelineException
from tests.conftest import decorator_mock

# Patch the file processing decorator before importing the module
with patch("db.file_processing_result.file_processing_result_to_db") as m_file_processing_result_to_db:
    def decorator_mock(step_name):
        def wrapper(func):
            return func
        return wrapper

    m_file_processing_result_to_db.side_effect = decorator_mock

    import pti_validation


@pytest.fixture(autouse=True, scope="module")
def m_db_manager():
    with patch("pti_validation.DbManager") as m_db:
        yield m_db

@patch("pti_validation.DatasetRevisionRepository")
@patch("pti_validation.S3")
@patch("pti_validation.TxcFileAttributesRepository")
@patch("pti_validation.PTIValidationService")
def test_lambda_hander(m_pti_validation_service, m_file_attribute_repo, m_s3, m_revision_repo):
    revision_id = 123
    event = {
        "Bucket": "test-bucket",
        "ObjectKey": "test-key",
        "DatasetRevisionId": revision_id,
    }

    revision = MagicMock(id=revision_id, dataset_id=2)
    m_revision_repo.return_value.get_by_id.return_value = revision

    s3_file_obj = MagicMock()
    m_s3.return_value.get_object.return_value = s3_file_obj

    txc_file_attributes = MagicMock()
    m_file_attribute_repo.return_value.get.return_value = txc_file_attributes

    result = pti_validation.lambda_handler(event, {})

    assert result == {"statusCode": 200}
    m_s3.return_value.get_object.assert_called_once_with(file_path="test-key")
    m_pti_validation_service.return_value.validate.assert_called_once_with(revision, s3_file_obj, txc_file_attributes)
    m_file_processing_result_to_db.assert_called_once_with(step_name=StepName.PTI_VALIDATION)


@patch("pti_validation.DatasetRevisionRepository")
@patch("pti_validation.S3")
@patch("pti_validation.TxcFileAttributesRepository")
@patch("pti_validation.PTIValidationService")
def test_lambda_hander_no_valid_files(m_pti_validation_service, m_file_attribute_repo, m_s3, m_revision_repo):
    revision_id = 123
    event = {
        "Bucket": "test-bucket",
        "ObjectKey": "test-key",
        "DatasetRevisionId": revision_id,
    }
    m_file_attribute_repo.return_value.get.return_value = None

    with pytest.raises(PipelineException):
        pti_validation.lambda_handler(event, {})

    m_file_processing_result_to_db.assert_called_once_with(step_name=StepName.PTI_VALIDATION)