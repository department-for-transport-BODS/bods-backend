from unittest.mock import MagicMock, patch

import pytest
from exceptions.pipeline_exceptions import PipelineException
from pti_validation import lambda_handler


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

    result = lambda_handler(event, {})

    assert result == {"statusCode": 200}
    m_s3.return_value.get_object.assert_called_once_with(file_path="test-key")
    m_pti_validation_service.return_value.validate.assert_called_once_with(revision, s3_file_obj, txc_file_attributes)


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
        lambda_handler(event, {})