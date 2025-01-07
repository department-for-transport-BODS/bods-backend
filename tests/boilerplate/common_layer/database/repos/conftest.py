from logging import DEBUG

import pytest
from common_layer.database.client import DatabaseSettings, PostgresSettings, SqlDB
from common_layer.database.create_tables import create_db_tables
from common_layer.db.bods_db import BodsDB
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def setup_db(caplog: pytest.LogCaptureFixture):
    """
    Session-scoped fixture to set up the database schema
    """
    postgres_settings = PostgresSettings(
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=54325,
        POSTGRES_DB="bodds_test",
        POSTGRES_USER="bodds_test",
        POSTGRES_PASSWORD="password",
    )

    db_settings = DatabaseSettings(postgres=postgres_settings)
    db = SqlDB(settings=db_settings)

    # Create tables once for the test session (existing tables will be skipped)
    with caplog.at_level(DEBUG):
        create_db_tables(db)

    yield db


@pytest.fixture()
def test_db(setup_db):
    """
    Function-scoped fixture for isolated db transactions in tests
    """
    db = setup_db

    # Start a new connection and transaction for the test
    connection = db.engine.connect()
    transaction = connection.begin()

    # Override the session factory to bind it to the test transaction
    db._session_factory = sessionmaker(bind=connection)

    yield db

    # Cleanup after the test
    transaction.rollback()
    connection.close()
