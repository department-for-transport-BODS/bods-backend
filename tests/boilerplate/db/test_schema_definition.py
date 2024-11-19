import pytest
from unittest import mock
from unittest.mock import patch
from db.schema_definition import (
    get_schema_definition_db_object,
    NoSchemaDefinition,
)
from db.models import PipelinesSchemadefinition


@patch("db.schema_definition.BodsDB")
def test_get_schema_definition_db_object_success(mock_bods_db):
    # Setup mock event and session
    mock_db_instance = mock_bods_db.return_value
    mock_session = mock.Mock()

    # Mock the context manager behavior (enter/exit)
    mock_db_instance.session.__enter__.return_value = mock_session
    mock_db_instance.session.__exit__.return_value = None

    # Mock the database query and session
    mock_db_instance.db.session = mock_session
    mock_schema_definition = mock.Mock(PipelinesSchemadefinition)
    mock_schema_definition.category = "CategoryA"  # Mocked category

    # Simulate that the query will return the mock schema_definition
    mock_session.query.return_value.where.return_value.first.return_value = (
        mock_schema_definition
    )

    # Call the function with a valid category
    result = get_schema_definition_db_object(mock_db_instance, "CategoryA")
    print(f"result: {result}")

    # Validate results
    assert result == mock_schema_definition
    mock_session.query.return_value.where.assert_called_once_with(
        mock_db_instance.db.classes.pipelines_schemadefinition.category == "CategoryA"
    )
    mock_session.query.return_value.where.return_value.first.assert_called_once()


@patch("db.schema_definition.BodsDB")
def test_get_schema_definition_db_object_not_found(mock_bods_db):
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

    # Call the function and assert the exception is raised
    with pytest.raises(NoSchemaDefinition):
        get_schema_definition_db_object(mock_db_instance, "CategoryA")


@patch("db.schema_definition.BodsDB")
def test_get_schema_definition_db_object_invalid_event(mock_bods_db):
    # Setup a mock event without a db session
    mock_db_instance = mock_bods_db.return_value
    mock_db_instance.session = None

    # Call the function and assert that it raises the expected exception
    with pytest.raises(ValueError):
        get_schema_definition_db_object(mock_db_instance, "CategoryA")
