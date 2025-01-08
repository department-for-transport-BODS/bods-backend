"""
Post Schema Check Local
"""

from pathlib import Path

import structlog
import typer
from common_layer.json_logging import configure_logging
from common_layer.txc.parser.parser_txc import parse_txc_file
from lxml import etree
from structlog.stdlib import get_logger

from src.timetables_etl.post_schema_check import run_post_schema_validations

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ]
)
app = typer.Typer()
log = get_logger()


def parse_xml_from_file(file_path: Path) -> etree._Element:
    """Parse XML document from local file"""
    try:
        return etree.parse(str(file_path)).getroot()
    except etree.XMLSyntaxError as e:
        log.error("XML Parsing Failed", file=str(file_path), error=str(e))
        raise


@app.command()
def validate(
    xml_file: Path = typer.Argument(
        ...,
        help="Path to XML file to validate",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    log_json: bool = typer.Option(
        False,
        "--log-json",
        help="Enable structured logging output",
    ),
):
    """Validate a TXC XML file against the 2.4 schema"""
    if log_json:
        configure_logging()

    try:
        # Load schema and parse XML
        txc_data = parse_txc_file(xml_file)

        violations = [
            v for v in run_post_schema_validations(txc_data) if not v.is_valid
        ]

        violation_count = len(violations)

        if violations:
            log.info(
                "Schema validation complete",
                status="failed",
                violation_count=violation_count,
                file=str(xml_file),
            )

            for idx, violation in enumerate(violations, 1):
                log.info(
                    "Schema violation details",
                    violation_number=f"{idx}/{violation_count}",
                    is_valid=violation.is_valid,
                    error_code=violation.error_code,
                    message=violation.message,
                )
            raise typer.Exit(1)

        log.info(
            "Post Schema validation complete",
            status="passed",
            violation_count=0,
            file=str(xml_file),
        )

    except (FileNotFoundError, etree.XMLSyntaxError, etree.XMLSchemaParseError) as e:
        log.error("Validation failed", error=str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
