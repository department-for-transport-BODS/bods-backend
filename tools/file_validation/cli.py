"""
Runs the File Attributes ETL Process against specified database
"""

from io import BytesIO
from pathlib import Path
from typing import List

import typer
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from timetables_etl.file_validation import dangerous_xml_check
from tools.common.xml_tools import get_xml_paths

app = typer.Typer()
log = get_logger()


def process_file_validation(xml_paths: List[Path]):
    """
    Process file validation
    """
    for xml_path in xml_paths:
        log.info("Processing XML File", path=xml_path)
        with open(xml_path, "rb") as file:
            dangerous_xml_check(BytesIO(file.read()))
            log.info("File validation passed", file_name=xml_path)


@app.command(name="file-validation")
def main(
    paths: list[Path] = typer.Argument(
        None,
        help="Paths to XML files or directories",
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
    try:
        process_file_validation(xml_paths)
    except Exception as e:
        log.error("File Validation failed.", error=str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
