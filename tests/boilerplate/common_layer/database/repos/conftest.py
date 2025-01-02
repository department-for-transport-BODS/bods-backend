import pytest
from common_layer.database.client import DatabaseSettings, PostgresSettings, SqlDB
from common_layer.database.create_tables import create_db_tables
from common_layer.db.bods_db import BodsDB
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def test_db():
    postgres_settings = PostgresSettings(
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="bodds",
        POSTGRES_USER="bodds_rw",
        POSTGRES_PASSWORD="password",
    )

    db_settings = DatabaseSettings(postgres=postgres_settings)
    db = SqlDB(settings=db_settings)

    # Create tables if they don't already exist
    create_db_tables(db)

    # Start a new connection and transaction for the test
    connection = db.engine.connect()
    transaction = connection.begin()

    # Override the session factory to bind it to the test transaction
    db._session_factory = sessionmaker(bind=connection)

    yield db

    # Cleanup after the test
    transaction.rollback()
    connection.close()
    db.engine.dispose()
