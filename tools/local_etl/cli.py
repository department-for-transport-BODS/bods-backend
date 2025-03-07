"""Test TXC transformation using SQLite database"""

import asyncio
from pathlib import Path

import boto3
import typer
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from tools.common.db_tools import create_db_config
from tools.common.models import TestConfig
from tools.common.xml_tools import get_xml_paths
from tools.local_etl.processing import process_files

app = typer.Typer()
log = get_logger()


@app.command(name="local-etl")
def main(
    paths: list[Path] = typer.Argument(
        None,
        help="Paths to XML files or directories",
    ),
    db_host: str = typer.Option(
        "localhost",
        "--db-host",
        help="Database host",
    ),
    db_name: str = typer.Option(
        "bods-local",
        "--db-name",
        help="Database name",
    ),
    db_user: str = typer.Option(
        "bods-local",
        "--db-user",
        help="Database user",
    ),
    db_password: str = typer.Option(
        "bods-local",
        "--db-password",
        help="Database password",
    ),
    db_port: int = typer.Option(
        5432,
        "--db-port",
        help="Database port",
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        help="Enable parallel processing",
    ),
    max_workers: int = typer.Option(
        10,
        "--max-workers",
        help="Maximum number of parallel workers (only used if --parallel is set)",
    ),
    log_json: bool = typer.Option(
        False,
        "--log-json",
        help="Enable Structured logging output",
    ),
    create_tables: bool = typer.Option(
        False,
        "--create-tables",
        help="Creates Tables via SQLAlchemy. Do not run on BODs DB managed by Django!",
    ),
    task_id: int | None = typer.Option(
        None,
        "--task-id",
        help="Optional task ID for processing",
    ),
    file_attributes_id: int | None = typer.Option(
        None,
        "--file-attributes-id",
        help="Optional file attributes ID",
    ),
    revision_id: int | None = typer.Option(
        None,
        "--revision-id",
        help="Optional revision ID",
    ),
    use_dotenv: bool = typer.Option(
        False,
        "--use-dotenv",
        help="Load database configuration from .env file",
    ),
    profile: str = typer.Option(
        "boddsdev", "--profile", help="AWS profile to use for dynamodb"
    ),
):
    """Transform TxC data into transmodel for testing"""
    if log_json:
        configure_logging()

    xml_paths = get_xml_paths(paths)

    try:
        db_config = create_db_config(
            use_dotenv, db_host, db_port, db_name, db_user, db_password
        )
    except ValueError as e:
        log.error("Database configuration error", error=str(e))
        raise typer.Exit(1)

    log.info("Running CLI with AWS profile", profile_name=profile)
    boto3.setup_default_session(profile_name=profile, region_name="eu-west-2")

    config = TestConfig(
        txc_paths=xml_paths,
        db_config=db_config,
        parallel=parallel,
        max_workers=max_workers,
        create_tables=create_tables,
        task_id=task_id,
        file_attributes_id=file_attributes_id,
        revision_id=revision_id,
    )

    asyncio.run(process_files(config))


if __name__ == "__main__":
    app()
