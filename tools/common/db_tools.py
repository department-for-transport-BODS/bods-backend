"""
CLI DB Helper Tools
"""

import os

import typer
from common_layer.database.client import (
    DatabaseBackend,
    DatabaseSettings,
    PostgresSettings,
    SqlDB,
)
from dotenv import load_dotenv
from structlog.stdlib import get_logger

from tools.common.models import DbConfig

log = get_logger()


def dotenv_loader():
    """
    Ensure that we load the .env from the project root
    """
    log.info("Loading dotenv")
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    env_path = os.path.join(project_root, ".env")

    if os.path.exists(env_path):
        log.info("Loading dotenv", path=env_path)
        load_dotenv(dotenv_path=env_path)
    else:
        log.warning("No .env file found", path=env_path)


def get_env_or_exit(var_name: str) -> str:
    """Get environment variable or exit if not found."""
    value = os.getenv(var_name)
    if not value:
        typer.echo(f"Error: {var_name} not found in environment variables")
        raise typer.Exit(1)
    return value


def create_db_config(
    use_dotenv: bool,
    db_host: str = "localhost",
    db_port: int = 5432,
    db_name: str = "bods-local",
    db_user: str = "bods-local",
    db_password: str = "bods-local",
) -> DbConfig:
    """
    Create database configuration either from .env file or provided parameters
    """
    if use_dotenv:

        dotenv_loader()
        try:
            port = int(get_env_or_exit("POSTGRES_PORT"))
        except ValueError:
            typer.echo("Error: POSTGRES_PORT must be a valid integer")
            raise typer.Exit(1)

        return DbConfig(
            host=get_env_or_exit("POSTGRES_HOST"),
            port=port,
            database=get_env_or_exit("POSTGRES_DB"),
            user=get_env_or_exit("POSTGRES_USER"),
            password=get_env_or_exit("POSTGRES_PASSWORD"),
        )

    return DbConfig(
        host=db_host, port=db_port, database=db_name, user=db_user, password=db_password
    )


def setup_db_instance(config: DbConfig) -> SqlDB:
    """Initialize database connection for each process"""
    pg_settings = PostgresSettings(
        POSTGRES_HOST=config.host,
        POSTGRES_DB=config.database,
        POSTGRES_USER=config.user,
        POSTGRES_PASSWORD=config.password,
        POSTGRES_PORT=config.port,
    )
    settings = DatabaseSettings(
        postgres=pg_settings,
    )
    return SqlDB(DatabaseBackend.POSTGRESQL, settings)
