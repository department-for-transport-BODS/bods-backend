from unittest.mock import MagicMock, patch

import pytest
from pti.service import PTIValidationService
from pti_common.models import Violation


@pytest.fixture(autouse=True, scope="module")
def m_dataset_repository():
    with patch("pti.service.DatasetRepository") as m_repo:
        yield m_repo


@patch("pti.service.PTIObservationRepository")
@patch("pti.service.TXCRevisionValidator")
@patch("pti.service.get_xml_file_pti_validator")
@patch("pti.service.TxcFileAttributesRepository")
def test_validate(m_file_attributes_repository, m_get_xml_file_pti_validator, m_txc_revision_validator, m_observation_repo):
    revision = MagicMock(id=123)
    xml_file = MagicMock()
    xml_file.read.return_value = b"dummycontent"
    txc_file_attributes = MagicMock()

    m_file_attributes_repository.return_value.exists.return_value = False

    violations = [
        Violation.model_construct(),
        Violation.model_construct(),
    ]
    m_get_xml_file_pti_validator.return_value.get_violations.return_value = violations
    m_txc_revision_validator.return_value.get_violations.return_value = ["txc_revision_violation"]

    service = PTIValidationService(db=MagicMock())
    service.validate(revision, xml_file, txc_file_attributes)

    m_get_xml_file_pti_validator.return_value.get_violations.assert_called_once_with(revision, xml_file)
    m_observation_repo.return_value.create.assert_called_once_with(revision.id, violations)

@patch("pti.service.PTIObservationRepository")
@patch("pti.service.sha1sum")
@patch("pti.service.TXCRevisionValidator")
@patch("pti.service.get_xml_file_pti_validator")
@patch("pti.service.TxcFileAttributesRepository")
def test_validate_unchanged_file(
    m_file_attributes_repository,
    m_get_xml_file_pti_validator,
    m_txc_revision_validator,
    m_sha1_sum,
    m_observation_repo,
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

    m_dataset = MagicMock()
    m_dataset_repository.return_value.get_by_id.return_value = m_dataset

    service = PTIValidationService(db=MagicMock())
    service.validate(revision, xml_file, txc_file_attributes)

    # We should look for the file in the live revision of the dataset
    m_file_attributes_repository.return_value.exists.assert_called_once_with(
        revision_id=m_dataset.live_revision_id, hash=m_sha1_sum.return_value
    )

    # Validations skipped
    m_get_xml_file_pti_validator.return_value.get_violations.assert_not_called()
    m_txc_revision_validator.return_value.get_violations.assert_not_called()

    # Observations not created
    m_observation_repo.return_value.create.assert_not_called()
