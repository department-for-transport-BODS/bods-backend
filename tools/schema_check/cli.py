"""
Run a Schema Check Against a TXC file
"""

from pathlib import Path
from unittest.mock import patch

import structlog
import typer
from common_layer.json_logging import configure_logging
from lxml import etree
from structlog.stdlib import get_logger

from src.common_lambdas.schema_check.app.schema_check import (
    SchemaCheckInputData,
    SchemaCheckSettings,
    process_schema_check,
)
from tools.common.db_tools import dotenv_loader

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


@app.command(name="schema-check")
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
    use_dotenv: bool = typer.Option(
        False,
        "--use-dotenv",
        help="Load configuration from .env file",
    ),
    log_json: bool = typer.Option(
        False,
        "--log-json",
        help="Enable structured logging output",
    ),
):
    """Validate a TXC XML file against the 2.4 schema for testing"""
    if log_json:
        configure_logging()

    if use_dotenv:
        dotenv_loader()

    settings = SchemaCheckSettings()
    log.info(
        "Running schema check for XML DATA TYPE:", data_type=settings.XML_DATA_TYPE
    )

    input = SchemaCheckInputData(
        DatasetRevisionId=revision_id,
        Bucket="dummy",
        ObjectKey="dummy",
    )

    try:
        # Parse XML doc from file instead of S3
        xml_doc = parse_xml_from_file(xml_file)
        with patch(
            "src.common_lambdas.schema_check.app.schema_check.parse_xml_from_s3",
            return_value=xml_doc,
        ):
            violations = process_schema_check(input)

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
