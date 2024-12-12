from src.boilerplate.common import BodsDB
from unittest.mock import patch
from os import environ
from pytest import raises
from psycopg2.errors import OperationalError

ENVIRONMENT_INPUT_TEST_VALUES = {
    "POSTGRES_HOST": "host",
    "POSTGRES_DB": "db",
    "POSTGRES_USER": "user",
    "POSTGRES_PORT": "5432",
    "POSTGRES_PASSWORD_ARN": "my_password_location_arn",
}

ENVIRONMENT_OUTPUT_TEST_VALUES = {
    "POSTGRES_HOST": "host",
    "POSTGRES_DB": "db",
    "POSTGRES_USER": "user",
    "POSTGRES_PORT": "5432",
    "POSTGRES_PASSWORD": "my_password",
}

ENVIRONMENT_INPUT_CONNECTION_VALUES = {
    "host": "host",
    "dbname": "db",
    "user": "user",
    "port": "5432",
    "password": "my_password",
}

ENVIRONMENT_OUTPUT_CONNECTION_VALUES = {
    "host": "host",
    "dbname": "db",
    "user": "user",
    "port": "5432",
    "password": "my_password",
    "sslmode": "require",
}


@patch("src.boilerplate.common.BodsDB._generate_rds_iam_auth_token")
@patch.dict(environ, ENVIRONMENT_INPUT_TEST_VALUES)
def test_connection_details_valid(mocked_db):
    mocked_db.return_value = "my_password"
    db = BodsDB()
    assert db._get_connection_details() == ENVIRONMENT_OUTPUT_CONNECTION_VALUES


environment_missing_test_values = dict(ENVIRONMENT_INPUT_TEST_VALUES)
environment_missing_test_values.pop("POSTGRES_HOST")


@patch("src.boilerplate.common.create_engine")
@patch("src.boilerplate.common.automap_base")
@patch.dict(environ, environment_missing_test_values)
def test_connection_details_missing(mock_automap_base, mock_create_engine, caplog):
    db = BodsDB()
    with raises(ValueError):
        print(db._get_connection_details())
    assert "host" in caplog.text


@patch(
    "src.boilerplate.common.BodsDB._get_connection_details",
    return_value=ENVIRONMENT_INPUT_CONNECTION_VALUES,
)
@patch("src.boilerplate.common.create_engine")
@patch("src.boilerplate.common.automap_base")
@patch("src.boilerplate.common.Session")
def test_database_initialisation(
    mock_session, mock_automap_base, mock_create_engine, connection_details
):
    mock_engine = mock_create_engine.return_value
    mock_base = mock_automap_base.return_value
    mock_session_instance = mock_session.return_value

    db = BodsDB()
    db._initialise_database()
    assert connection_details.called
    assert mock_create_engine.called
    assert mock_automap_base.called
    assert mock_session.called
    mock_create_engine.assert_called_once_with(
        f"postgresql+psycopg2://{ENVIRONMENT_INPUT_TEST_VALUES['POSTGRES_USER']}:"
        f"{ENVIRONMENT_OUTPUT_TEST_VALUES['POSTGRES_PASSWORD']}@"
        f"{ENVIRONMENT_OUTPUT_TEST_VALUES['POSTGRES_HOST']}:"
        f"{ENVIRONMENT_OUTPUT_TEST_VALUES['POSTGRES_PORT']}/"
        f"{ENVIRONMENT_OUTPUT_TEST_VALUES['POSTGRES_DB']}"
    )
    mock_session.assert_called_once_with(mock_engine)
    assert db.session is not None
    assert db.classes is not None


@patch(
    "src.boilerplate.common.BodsDB._get_connection_details",
    return_value=ENVIRONMENT_OUTPUT_TEST_VALUES,
)
@patch("src.boilerplate.common.create_engine")
@patch("src.boilerplate.common.automap_base")
@patch("src.boilerplate.common.Session", side_effect=OperationalError())
def test_database_initialisation_failed(
    connection_details, create_engine, automap_base, session, caplog
):
    # connection_details.return_value = ENVIRONMENT_INPUT_TEST_VALUES
    automap_base.prepare.return_value = True
    db = BodsDB()
    with raises(OperationalError):
        db._initialise_database()
        assert "Failed to connect to DB" in caplog.text
