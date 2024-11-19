from unittest.mock import MagicMock, patch

import pytest
from pti.service import PTIValidationService


@pytest.fixture(autouse=True, scope="module")
def m_db_manager():
    with patch("pti.service.DbManager") as m_db:
        yield m_db


@pytest.fixture(autouse=True, scope="module")
def m_dataset_repository():
    with patch("pti.service.DatasetRepository") as m_repo:
        yield m_repo


@patch("pti.service.TXCRevisionValidator")
@patch("pti.service.get_xml_file_pti_validator")
@patch("pti.service.TxcFileAttributesRepository")
def test_validate(m_file_attributes_repository, m_get_xml_file_pti_validator, m_txc_revision_validator):
    revision = MagicMock()
    xml_file = MagicMock()
    xml_file.read.return_value = b"dummycontent"
    txc_file_attributes = MagicMock()

    m_file_attributes_repository.return_value.exists.return_value = False

    m_get_xml_file_pti_validator.return_value.get_violations.return_value = [
        "xml_file_violation_1",
        "xml_file_violation_2",
    ]
    m_txc_revision_validator.return_value.get_violations.return_value = ["txc_revision_violation"]

    service = PTIValidationService(db=MagicMock())
    service.validate(revision, xml_file, txc_file_attributes)

    m_get_xml_file_pti_validator.return_value.get_violations.assert_called_once_with(revision, xml_file)


@patch("pti.service.sha1sum")
@patch("pti.service.TXCRevisionValidator")
@patch("pti.service.get_xml_file_pti_validator")
@patch("pti.service.TxcFileAttributesRepository")
def test_validate_unchanged_file(
    m_file_attributes_repository,
    m_get_xml_file_pti_validator,
    m_txc_revision_validator,
    m_sha1_sum,
    m_dataset_repository,
):
    """
    Validation should be skipped for unchanged files
    """
    revision = MagicMock(id=123)
    xml_file = MagicMock()
    xml_file.read.return_value = b"dummycontent"
    txc_file_attributes = MagicMock()

    m_file_attributes_repository.return_value.exists.return_value = True

    service = PTIValidationService(db=MagicMock())
    service.validate(revision, xml_file, txc_file_attributes)

    # We should look for the file in the live revision of the dataset
    m_dataset = m_dataset_repository.return_value.get_by_id.return_value
    m_file_attributes_repository.return_value.exists.assert_called_once_with(
        revision_id=m_dataset.live_revision_id, hash=m_sha1_sum.return_value
    )

    # Validations skipped
    m_get_xml_file_pti_validator.return_value.get_violations.assert_not_called()
    m_txc_revision_validator.return_value.get_violations.assert_not_called()
