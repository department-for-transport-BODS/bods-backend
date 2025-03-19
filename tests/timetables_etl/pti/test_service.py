"""
Test PTI Service Validation
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.client import SqlDB
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.exceptions import PTIViolationFound
from common_layer.xml.txc.models.txc_data import TXCData
from pti.app.models.models_pti import PtiObservation, PtiRule, PtiViolation
from pti.app.models.models_pti_task import DbClients
from pti.app.service import PTIValidationService

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


@pytest.fixture
def txc_file_attributes():
    """
    Return an instance of txc file attrictures
    """
    return TXCFileAttributes(
        id=456,
        revision_number=1,
        service_code="Service1",
        line_names=[],
        modification_datetime=datetime(2025, 1, 1),
        hash="filehash",
        filename="filename.xml",
    )


@pytest.fixture
def m_db_clients() -> DbClients:
    """
    Return instance of DbClients containing mocked clients
    """
    return DbClients(
        sql_db=MagicMock(spec=SqlDB),
        dynamodb=MagicMock(spec=DynamoDBCache),
        stop_point_client=MagicMock(spec=NaptanStopPointDynamoDBClient),
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
    m_db_clients,
):
    revision = OrganisationDatasetRevisionFactory.create_with_id(id_number=123)
    xml_file = MagicMock()
    xml_file.read.return_value = b"dummycontent"
    violations = [
        PtiViolation(
            line=42,
            filename="route.xml",
            name="StopPoint",
            element_text="<StopPoint>",
            observation=PtiObservation(
                details="Invalid stop point",
                category="Schema",
                service_type="bus",
                reference="PTI-0001",
                context="ValidationContext",
                number=1,
                rules=[PtiRule(test="validate_stop_point")],
            ),
        ),
        PtiViolation(
            line=78,
            filename="route.xml",
            name="JourneyPattern",
            element_text="<JourneyPattern>",
            observation=PtiObservation(
                details="Invalid pattern",
                category="Timing",
                service_type="bus",
                reference="PTI-0023",
                context="ValidationContext",
                number=2,
                rules=[PtiRule(test="validate_journey_pattern")],
            ),
        ),
    ]
    m_get_xml_file_pti_validator.return_value.get_violations.return_value = violations
    m_txc_revision_validator.return_value.get_violations.return_value = violations

    service = PTIValidationService(
        db_clients=m_db_clients,
        live_revision_attributes=[],
    )

    with pytest.raises(
        PTIViolationFound, match="PTI validation failed due to violations"
    ):
        service.validate(
            revision, xml_file, txc_file_attributes, TXCData.model_construct()
        )

    m_get_xml_file_pti_validator.return_value.get_violations.assert_called_once_with(
        revision, xml_file
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
    m_db_clients,
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
        db_clients=m_db_clients,
        live_revision_attributes=live_file_attributes,
    )
    service.validate(revision, xml_file, txc_file_attributes, TXCData.model_construct())

    m_sha1_sum.assert_called_once_with(xml_file.read.return_value)

    # Validations skipped
    m_get_xml_file_pti_validator.return_value.get_violations.assert_not_called()
    m_txc_revision_validator.return_value.get_violations.assert_not_called()

    # Observations not created
    m_observation_repo.return_value.create_from_violations.assert_not_called()
