"""
Run a Schema Check Against a TXC file
"""

from pathlib import Path

import structlog
import typer
from common_layer.json_logging import configure_logging
from lxml import etree
from schema_check.app.schema_check import get_schema_violations, load_txc_schema
from structlog.stdlib import get_logger

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
    revision_id: int = typer.Option(
        1,
        "--revision-id",
        "-r",
        help="Optional revision ID for tracking violations (defaults to 1)",
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
        schema = load_txc_schema()
        xml_doc = parse_xml_from_file(xml_file)

        # Validate and get violations
        violations = get_schema_violations(schema, xml_doc, revision_id)

        # Output results
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
                    line=violation.line,
                    details=violation.details,
                    filename=violation.filename,
                )
            raise typer.Exit(1)

        log.info(
            "Schema validation complete",
            status="passed",
            violation_count=0,
            file=str(xml_file),
        )

    except (FileNotFoundError, etree.XMLSyntaxError, etree.XMLSchemaParseError) as e:
        log.error("Validation failed", error=str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
