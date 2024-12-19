"""
CLI DB Helper Tools
"""

from common_layer.database.client import (
    DatabaseBackend,
    DatabaseSettings,
    PostgresSettings,
    SqlDB,
)

from tools.common.models import TestConfig


def setup_process_db(config: TestConfig) -> SqlDB:
    """Initialize database connection for each process"""
    pg_settings = PostgresSettings(
        POSTGRES_HOST=config.db_host,
        POSTGRES_DB=config.db_name,
        POSTGRES_USER=config.db_user,
        POSTGRES_PASSWORD=config.db_password,
        POSTGRES_PORT=config.db_port,
    )
    settings = DatabaseSettings(
        postgres=pg_settings,
    )
    return SqlDB(DatabaseBackend.POSTGRESQL, settings)
