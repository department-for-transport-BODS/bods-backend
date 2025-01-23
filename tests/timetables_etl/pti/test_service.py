"""
Test PTI Service Validation
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.pti.models import Violation
from pti.app.service import PTIValidationService

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


@pytest.fixture
def txc_file_attributes():
    return TXCFileAttributes(
        id=456,
        revision_number=1,
        service_code="Service1",
        line_names=[],
        modification_datetime=datetime(2025, 1, 1),
        hash="filehash",
        filename="filename.xml",
    )


@patch("pti.app.service.OrganisationTXCFileAttributesRepo")
@patch("pti.app.service.DataQualityPTIObservationRepo")
@patch("pti.app.service.TXCRevisionValidator")
@patch("pti.app.service.get_xml_file_pti_validator")
def test_validate(
    m_get_xml_file_pti_validator,
    m_txc_revision_validator,
    m_observation_repo,
    m_file_attributes_repo,
    txc_file_attributes,
):
    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=123)
    xml_file = MagicMock()
    xml_file.read.return_value = b"dummycontent"
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

    with pytest.raises(ValueError, match="PTI validation failed due to violations"):
        service.validate(revision, xml_file, txc_file_attributes)

    m_get_xml_file_pti_validator.return_value.get_violations.assert_called_once_with(
        revision, xml_file
    )
    m_observation_repo.return_value.create_from_violations.assert_called_once_with(
        revision.id, violations
    )
    m_file_attributes_repo.return_value.delete_by_id.assert_called_once_with(
        txc_file_attributes.id
    )


@patch("pti.app.service.DataQualityPTIObservationRepo")
@patch("pti.app.service.sha1sum")
@patch("pti.app.service.TXCRevisionValidator")
@patch("pti.app.service.get_xml_file_pti_validator")
def test_validate_unchanged_file(
    m_get_xml_file_pti_validator,
    m_txc_revision_validator,
    m_sha1_sum,
    m_observation_repo,
    txc_file_attributes,
):
    """
    Validation should be skipped for unchanged files
    """
    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=123)
    xml_file = MagicMock()
    xml_file.read.return_value = b"dummycontent"

    existing_file_hash = txc_file_attributes.hash
    m_sha1_sum.return_value = existing_file_hash

    live_file_attributes = [
        TXCFileAttributes(
            id=457,
            revision_number=2,
            service_code="Service1",
            line_names=[],
            modification_datetime=datetime(2025, 1, 10),
            hash=existing_file_hash,
            filename="filename.xml",
        )
    ]

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
    m_observation_repo.return_value.create_from_violations.assert_not_called()
