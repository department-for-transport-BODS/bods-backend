"""
Runs the File Attributes ETL Process against specified database
"""

from pathlib import Path

import typer
from common_layer.database.client import SqlDB
from common_layer.json_logging import configure_logging
from common_layer.xml.txc.parser.parser_txc import TXCParserConfig, parse_txc_file
from structlog.stdlib import get_logger

from src.timetables_etl.file_attributes_etl.app.file_attributes_etl import (
    process_file_attributes,
)
from src.timetables_etl.file_attributes_etl.app.models import FileAttributesInputData
from tools.common.db_tools import create_db_config, setup_db_instance
from tools.common.xml_tools import get_xml_paths

app = typer.Typer()
log = get_logger()


PARSER_CONFIG = TXCParserConfig(file_hash=True)


def process_txc(xml_paths: list[Path], revision_id: int, db: SqlDB) -> list[int]:
    """
    Process file attributes
    """

    created_file_attribute_ids: list[int] = []
    for xml_path in xml_paths:
        input_data = FileAttributesInputData(
            DatasetRevisionId=revision_id, Bucket="Test", ObjectKey=str(xml_path)
        )
        log.info("Processing XML File", path=xml_path)
        txc_data = parse_txc_file(xml_path, PARSER_CONFIG)
        try:
            txc_file_attributes = process_file_attributes(input_data, txc_data, db)
            created_file_attribute_ids.append(txc_file_attributes.id)
        except ValueError as e:
            log.error("Revision ID Not found, can't add File Attributes", error=str(e))
    return created_file_attribute_ids


@app.command(name="file-attributes")
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
    use_dotenv: bool = typer.Option(
        False,
        "--use-dotenv",
        help="Load database configuration from .env file",
    ),
):
    """Process TXC XML file to parse TxC data for testing"""
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
    db = setup_db_instance(db_config)
    txc_file_attributes_ids = process_txc(xml_paths, revision_id, db)
    log.info(
        "Created TXCFileAttributes",
        txc_file_attributes_ids=txc_file_attributes_ids,
    )


if __name__ == "__main__":
    app()
