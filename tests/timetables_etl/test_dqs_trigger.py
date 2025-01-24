from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from common_layer.db.constants import StepName
from common_layer.exceptions.pipeline_exceptions import PipelineException
from dqs_trigger import lambda_handler


# Mock the Lambda handler dependencies
@pytest.fixture
def mock_db():
    with patch("dqs_trigger.SqlDB") as mock_db_instance:
        yield mock_db_instance

@pytest.fixture
def mock_s3_client():
    with patch("dqs_trigger.StepFunctionsClientWrapper") as mock_s3_instance:
        yield mock_s3_instance

@pytest.fixture
def mock_repos(mock_db):
    # Mock the repositories used in lambda_handler
    with patch("dqs_trigger.OrganisationDatasetRevisionRepo") as m_revision_repo, \
         patch("dqs_trigger.DQSReportRepo") as m_report_repo, \
         patch("dqs_trigger.OrganisationTXCFileAttributesRepo") as m_txc_file_repo:
        
        # Mocks for methods in the repo classes
        m_revision_repo.return_value.get_by_id.return_value = MagicMock(id=123)
        m_report_repo.return_value.get_by_revision_id.return_value = None
        m_txc_file_repo.return_value.get_by_revision_id.return_value = [
            MagicMock(id=1), MagicMock(id=2)
        ]
        
        yield m_revision_repo, m_report_repo, m_txc_file_repo

def test_lambda_handler_success(mock_db, mock_repos, mock_s3_client):
    # Arrange
    event = {
        "DatasetRevisionId": 442
    }

    # Mock methods for the function
    m_revision_repo, m_report_repo, m_txc_file_repo = mock_repos

    # Create a mock of the DQSReportRepo's create_report_for_revision method
    m_report_repo.return_value.create_report_for_revision.return_value = None
    mock_s3_client.return_value.start_execution.return_value = "mock-execution-arn"

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response == {"statusCode": 200}
    m_revision_repo.return_value.get_by_id.assert_called_once_with(442)
    m_report_repo.return_value.create_report_for_revision.assert_called_once()
    mock_s3_client.return_value.start_execution.assert_called_with(
        state_machine_arn="",
        input={"file_id": 1},
        name="DQSExecutionForRevision1"
    )

def test_lambda_handler_revision_not_found(mock_db, mock_repos):
    # Arrange
    event = {
        "DatasetRevisionId": 442
    }
    m_revision_repo, m_report_repo, m_txc_file_repo = mock_repos

    # Mock get_by_id to return None, simulating the revision not found
    m_revision_repo.return_value.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PipelineException, match="No revision with id 442 found"):
        lambda_handler(event, None)

def test_lambda_handler_no_txc_file_attributes(mock_db, mock_repos, mock_s3_client):
    # Arrange
    event = {
        "DatasetRevisionId": 442
    }
    m_revision_repo, m_report_repo, m_txc_file_repo = mock_repos

    # Mock get_by_revision_id to return an empty list, simulating no TXC file attributes
    m_txc_file_repo.return_value.get_by_revision_id.return_value = []

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response == {"statusCode": 200}
    m_txc_file_repo.return_value.get_by_revision_id.assert_called_once_with(442)
    mock_s3_client.return_value.start_execution.assert_not_called()

def test_lambda_handler_initialise_dqs_report(mock_db, mock_repos):
    # Arrange
    event = {
        "DatasetRevisionId": 442
    }
    m_revision_repo, m_report_repo, m_txc_file_repo = mock_repos

    # Create a mock of the DQSReportRepo's delete_report_by_revision_id method
    m_report_repo.return_value.delete_report_by_revision_id.return_value = None
    m_report_repo.return_value.create_report_for_revision.return_value = None

    # Act
    lambda_handler(event, None)

    # Assert
    m_report_repo.return_value.delete_report_by_revision_id.assert_called_once_with(442)
    m_report_repo.return_value.create_report_for_revision.assert_called_once()
