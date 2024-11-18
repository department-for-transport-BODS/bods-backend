import pytest
from unittest import mock
from unittest.mock import patch
from db.dataset_revision import get_dataset_revision, BodsDB, NoRowFound
from db.models import OrganisationDatasetrevision


@patch("db.dataset_revision.BodsDB")
def test_get_dataset_revision_success(mock_bods_db):
    mock_db_instance = mock_bods_db.return_value
    mock_session = mock.Mock()

    # Mock the context manager behavior (enter/exit)
    mock_db_instance.session.__enter__.return_value = mock_session
    mock_db_instance.session.__exit__.return_value = None

    # Mock the database query and session
    mock_db_instance.db.session = mock_session
    mock_dataset_revision = mock.Mock(OrganisationDatasetrevision)
    mock_dataset_revision.id = 123

    # Simulate that the query will return the mock dataset_revision
    mock_session.query.return_value.where.return_value.first.return_value = (
        mock_dataset_revision
    )

    # Call the function
    result = get_dataset_revision(mock_db_instance, 123)

    # Validate results
    assert result == mock_dataset_revision
    # mock_session.query.assert_called_once_with(
    #     mock_db_instance.db.classes.organisation_datasetrevision
    # )
    mock_session.query.return_value.where.assert_called_once_with(
        mock_db_instance.db.classes.organisation_datasetrevision.id == 123
    )
    mock_session.query.return_value.where.return_value.first.assert_called_once()


@patch("db.dataset_revision.BodsDB")
def test_get_dataset_revision_not_found(mock_bods_db):
    # Setup mock event and session
    mock_db_instance = mock_bods_db.return_value
    mock_session = mock.Mock()

    # Mock the context manager behavior (enter/exit)
    mock_db_instance.session.__enter__.return_value = mock_session
    mock_db_instance.session.__exit__.return_value = None

    # Mock the database query and session
    mock_db_instance.db.session = mock_session

    # Simulate that the query will return None (no record found)
    mock_session.query.return_value.where.return_value.first.return_value = None

    # Call the function and assert the exception
    with pytest.raises(NoRowFound):
        get_dataset_revision(mock_db_instance, 999)


@patch("db.dataset_revision.BodsDB")
def test_get_dataset_revision_invalid_event(mock_bods_db):
    # Setup a mock event without a db session
    mock_db_instance = mock_bods_db.return_value
    mock_db_instance.session = None

    with pytest.raises(ValueError, match="No database session provided"):
        get_dataset_revision(mock_db_instance, 123)
