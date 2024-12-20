"""
Runs the File Attributes ETL Process against specified database
"""

from pathlib import Path

import typer
from common_layer.database.client import SqlDB
from common_layer.json_logging import configure_logging
from common_layer.txc.parser.parser_txc import parse_txc_file
from structlog.stdlib import get_logger

from timetables_etl.file_attributes_etl import (
    FileAttributesInputData,
    process_file_attributes,
)
from tools.common.db_tools import setup_process_db
from tools.common.models import TestConfig
from tools.common.xml_tools import get_xml_paths

app = typer.Typer()
log = get_logger()


def process_txc(xml_paths: list[Path], revision_id: int, db: SqlDB):
    """
    Process file attributes
    """
    input_data = FileAttributesInputData(
        DatasetRevisionId=revision_id, Bucket="Test", ObjectKey="Test"
    )

    for xml_path in xml_paths:
        log.info("Processing XML File", path=xml_path)
        txc_data = parse_txc_file(xml_path, False, True)
        try:
            process_file_attributes(input_data, txc_data, db)
        except ValueError as e:
            log.error("Revision ID Not found, can't add File Attributes", error=str(e))


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
    revision_id: int = typer.Option(
        5432,
        "--revision-id",
        help="The Revision ID to use",
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
    )
    db = setup_process_db(config)
    process_txc(xml_paths, revision_id, db)


if __name__ == "__main__":
    app()
