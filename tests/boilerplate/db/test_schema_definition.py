import pytest
from unittest import mock
from db.schema_definition import (
    get_schema_definition_db_object,
    LambdaEvent,
    NoSchemaDefinitionError,
    SchemaCategory,
)
from db.models import PipelinesSchemadefinition


def test_get_schema_definition_db_object_success():
    # Setup mock event and session
    mock_event = mock.Mock(LambdaEvent)
    mock_session = mock.Mock()

    # Mock the context manager behavior (enter/exit)
    mock_session.__enter__ = mock.Mock(return_value=mock_session)
    mock_session.__exit__ = mock.Mock(return_value=None)

    # Mock the database query and session
    mock_event.db.session = mock_session
    mock_schema_definition = mock.Mock(PipelinesSchemadefinition)
    mock_schema_definition.category = "CategoryA"  # Mocked category

    # Simulate that the query will return the mock schema_definition
    mock_session.query.return_value.where.return_value.first.return_value = (
        mock_schema_definition
    )

    # Call the function with a valid category
    result = get_schema_definition_db_object(mock_event, "CategoryA")

    # Validate results
    assert result == mock_schema_definition
    mock_session.query.assert_called_once_with(
        mock_event.db.classes.pipelines_schemadefinition
    )
    mock_session.query.return_value.where.assert_called_once_with(
        mock_event.db.classes.pipelines_schemadefinition.category == "CategoryA"
    )
    mock_session.query.return_value.where.return_value.first.assert_called_once()


def test_get_schema_definition_db_object_not_found():
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

    # Call the function and assert the exception is raised
    with pytest.raises(NoSchemaDefinitionError):
        get_schema_definition_db_object(mock_event, "CategoryA")


def test_get_schema_definition_db_object_invalid_event():
    # Setup a mock event without a db session
    mock_event = mock.Mock(LambdaEvent)
    mock_event.db.session = None  # Simulate missing db session

    # Call the function and assert that it raises an exception (AttributeError or custom)
    with pytest.raises(ValueError, match="No database session provided"):
        get_schema_definition_db_object(mock_event, "CategoryA")
