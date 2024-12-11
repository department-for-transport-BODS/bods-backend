"""Test TXC transformation using SQLite database"""

import asyncio
from pathlib import Path

import typer
from structlog.stdlib import get_logger

from timetables_etl.etl.app.log_setup import configure_logging
from tools.local_etl.models import TestConfig
from tools.local_etl.processing import process_files

app = typer.Typer()
log = get_logger()


def get_xml_paths(paths: list[Path]) -> list[Path]:
    """Process provided paths to handle both files and directories"""
    xml_paths: list[Path] = []

    if not paths:
        log.info("No paths provided, using default test files")
    else:
        for path in paths:
            if path.is_dir():
                xml_paths.extend(path.glob("**/*.xml"))
            elif path.is_file() and path.suffix.lower() == ".xml":
                xml_paths.append(path)
            else:
                log.warning("Skipping invalid path", path=path)

    if not xml_paths:
        log.error("No valid XML files found in the specified paths", paths=paths)
        raise typer.Exit(code=1)

    return xml_paths


@app.command()
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
):
    """Process TXC XML files for transformation testing"""
    if log_json:
        configure_logging()

    xml_paths = get_xml_paths(paths)
    config = TestConfig(
        txc_paths=xml_paths,
        db_host=db_host,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        db_port=db_port,
        parallel=parallel,
        max_workers=max_workers,
    )

    asyncio.run(process_files(config))


if __name__ == "__main__":
    app()
