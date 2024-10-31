from boilerplate.common import BodsDB
from unittest.mock import patch
from os import environ
from pytest import raises
from psycopg2.errors import OperationalError

# Define test environment variables and expected output values
ENVIRONMENT_INPUT_TEST_VALUES = {
    "POSTGRES_HOST": "host",
    "POSTGRES_DB": "db",
    "POSTGRES_USER": "user",
    "POSTGRES_PORT": "5432",
    "POSTGRES_PASSWORD": "my_password"
}

ENVIRONMENT_OUTPUT_TEST_VALUES = {
    "host": "host",
    "dbname": "db",
    "user": "user",
    "port": "5432",
    "password": "my_password",
    "sslmode": "require",
}

@patch("boilerplate.common.BodsDB._generate_rds_iam_auth_token", return_value="my_password")
@patch.dict(environ, ENVIRONMENT_INPUT_TEST_VALUES, clear=True)
def test_connection_details_valid(mocked_db_token):
    # Initialise DB and fetch connection details
    db = BodsDB()
    connection_details = db._get_connection_details()
    # Validate the output matches the expected environment values
    assert connection_details == ENVIRONMENT_OUTPUT_TEST_VALUES

# Test case for missing environment variable scenario
@patch.dict(environ, {k: v for k, v in ENVIRONMENT_INPUT_TEST_VALUES.items() if k != "POSTGRES_HOST"}, clear=True)
def test_connection_details_missing(caplog):
    db = BodsDB()
    with raises(ValueError):
        db._get_connection_details()
    # Check that the appropriate error message is logged
    assert "Missing connection details value: host" in caplog.text

@patch("boilerplate.common.BodsDB._get_connection_details", return_value=ENVIRONMENT_OUTPUT_TEST_VALUES)
@patch("boilerplate.common.create_engine")
@patch("boilerplate.common.automap_base")
@patch("boilerplate.common.sessionmaker")
def test_database_initialisation(mock_sessionmaker, mock_automap_base, mock_create_engine, mock_connection_details):
    # Initialise DB and trigger engine initialisation
    db = BodsDB()
    db._initialise_engine()
    
    # Check that the engine is created with the expected connection string
    mock_create_engine.assert_called_once_with(
        f"postgresql+psycopg2://{ENVIRONMENT_INPUT_TEST_VALUES['POSTGRES_USER']}:"
        f"{ENVIRONMENT_INPUT_TEST_VALUES['POSTGRES_PASSWORD']}@"
        f"{ENVIRONMENT_INPUT_TEST_VALUES['POSTGRES_HOST']}:"
        f"{ENVIRONMENT_INPUT_TEST_VALUES['POSTGRES_PORT']}/"
        f"{ENVIRONMENT_INPUT_TEST_VALUES['POSTGRES_DB']}?sslmode=require"
    )
    # Verify that session and classes properties are accessible and initialised
    assert db.session is not None
    assert db.classes is not None

@patch("boilerplate.common.BodsDB._get_connection_details", return_value=ENVIRONMENT_OUTPUT_TEST_VALUES)
@patch("boilerplate.common.create_engine", side_effect=OperationalError)
@patch("boilerplate.common.automap_base")
@patch("boilerplate.common.sessionmaker")
def test_database_initialisation_failed(mock_sessionmaker, mock_automap_base, mock_create_engine, mock_connection_details, caplog):
    db = BodsDB()
    # Attempting to initialise the engine should raise an OperationalError
    with raises(OperationalError):
        db._initialise_engine()
    # Ensure the appropriate error message is logged
    assert "Failed to initialise SQLAlchemy engine" in caplog.text
