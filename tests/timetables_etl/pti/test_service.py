from unittest.mock import MagicMock, patch

import pytest
from common_layer.pti.models import Violation
from pti.service import PTIValidationService


@patch("pti.service.PTIObservationRepository")
@patch("pti.service.TXCRevisionValidator")
@patch("pti.service.get_xml_file_pti_validator")
def test_validate(
    m_get_xml_file_pti_validator, m_txc_revision_validator, m_observation_repo
):
    revision = MagicMock(id=123)
    xml_file = MagicMock()
    xml_file.read.return_value = b"dummycontent"
    txc_file_attributes = MagicMock()

    violations = [
        Violation.model_construct(),
        Violation.model_construct(),
    ]
    m_get_xml_file_pti_validator.return_value.get_violations.return_value = violations
    m_txc_revision_validator.return_value.get_violations.return_value = [
        "txc_revision_violation"
    ]

    service = PTIValidationService(
        db=MagicMock(), dynamodb=MagicMock(), live_revision_attributes=[]
    )
    service.validate(revision, xml_file, txc_file_attributes)

    m_get_xml_file_pti_validator.return_value.get_violations.assert_called_once_with(
        revision, xml_file
    )
    m_observation_repo.return_value.create.assert_called_once_with(
        revision.id, violations
    )


@patch("pti.service.PTIObservationRepository")
@patch("pti.service.sha1sum")
@patch("pti.service.TXCRevisionValidator")
@patch("pti.service.get_xml_file_pti_validator")
def test_validate_unchanged_file(
    m_get_xml_file_pti_validator,
    m_txc_revision_validator,
    m_sha1_sum,
    m_observation_repo,
):
    """
    Validation should be skipped for unchanged files
    """
    revision = MagicMock(id=123)
    xml_file = MagicMock()
    xml_file.read.return_value = b"dummycontent"

    existing_file_hash = "file-hash"
    m_sha1_sum.return_value = existing_file_hash

    txc_file_attributes = MagicMock()
    live_file_attributes = [MagicMock(hash=existing_file_hash)]

    service = PTIValidationService(
        db=MagicMock(),
        dynamodb=MagicMock(),
        live_revision_attributes=live_file_attributes,
    )
    service.validate(revision, xml_file, txc_file_attributes)

    m_sha1_sum.assert_called_once_with(xml_file.read.return_value)

    # Validations skipped
    m_get_xml_file_pti_validator.return_value.get_violations.assert_not_called()
    m_txc_revision_validator.return_value.get_violations.assert_not_called()

    # Observations not created
    m_observation_repo.return_value.create.assert_not_called()
