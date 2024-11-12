import pytest
from unittest import mock
from db.dataset_revision import get_dataset_revision, LambdaEvent, NoDataFoundError
from db.models import OrganisationDatasetrevision


def test_get_dataset_revision_success():
    mock_event = mock.Mock(LambdaEvent)
    mock_session = mock.Mock()

    # Mock the context manager behavior (enter/exit)
    mock_session.__enter__ = mock.Mock(return_value=mock_session)
    mock_session.__exit__ = mock.Mock(return_value=None)

    # Mock the database query and session
    mock_event.db.session = mock_session
    mock_dataset_revision = mock.Mock(OrganisationDatasetrevision)
    mock_dataset_revision.id = 123

    # Simulate that the query will return the mock dataset_revision
    mock_session.query.return_value.where.return_value.first.return_value = (
        mock_dataset_revision
    )

    # Call the function
    result = get_dataset_revision(mock_event, 123)

    # Validate results
    assert result == mock_dataset_revision
    mock_session.query.assert_called_once_with(
        mock_event.db.classes.organisation_datasetrevision
    )
    mock_session.query.return_value.where.assert_called_once_with(
        mock_event.db.classes.organisation_datasetrevision.id == 123
    )
    mock_session.query.return_value.where.return_value.first.assert_called_once()


def test_get_dataset_revision_not_found():
    # Setup mock event and session
    mock_event = mock.Mock(LambdaEvent)
    mock_session = mock.Mock()

    # Mock the context manager behavior (enter/exit)
    mock_session.__enter__ = mock.Mock(return_value=mock_session)
    mock_session.__exit__ = mock.Mock(return_value=None)

    # Mock the database query and session
    mock_event.db.session = mock_session

    # Simulate that the query will return None (no record found)
    mock_session.query.return_value.where.return_value.first.return_value = None

    # Call the function and assert the exception
    with pytest.raises(NoDataFoundError):
        get_dataset_revision(mock_event, 999)


def test_get_dataset_revision_invalid_event():
    # Setup a mock event without a db session
    mock_event = mock.Mock(LambdaEvent)
    mock_event.db.session = None

    with pytest.raises(ValueError, match="No database session provided"):
        get_dataset_revision(mock_event, 123)
