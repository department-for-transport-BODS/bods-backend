"""
SqlDB Test DB
"""

from typing import Generator

import pytest
from common_layer.database.client import DatabaseSettings, PostgresSettings, SqlDB
from common_layer.database.create_tables import create_db_tables
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session", name="setup_db")
def setup_db_fixture() -> SqlDB:
    """
    Session-scoped fixture that configures and initializes the test database schema once
    """
    postgres_settings = PostgresSettings(
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="bodds_test",
        POSTGRES_USER="bodds_test",
        POSTGRES_PASSWORD="password",
    )

    db_settings = DatabaseSettings(postgres=postgres_settings)
    db = SqlDB(settings=db_settings)

    create_db_tables(db)
    return db


@pytest.fixture()
def test_db(setup_db: SqlDB) -> Generator[SqlDB, None, None]:
    """
    Function-scoped fixture for isolated db transactions in tests
    """
    db = setup_db

    # Start a new connection and transaction for the test
    connection = db.engine.connect()
    transaction = connection.begin()

    # Override the session factory to bind it to the test transaction
    db._session_factory = sessionmaker(  # pylint: disable=protected-access
        bind=connection
    )

    yield db

    # Cleanup after the test
    transaction.rollback()
    connection.close()
