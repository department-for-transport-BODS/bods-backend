"""
SchemaCheckLambda
"""

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import BotoCoreError, ClientError
from common_layer.database.client import SqlDB
from common_layer.database.models.model_data_quality import DataQualitySchemaViolation
from common_layer.database.repos.repo_data_quality import DataQualitySchemaViolationRepo
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from lxml.etree import _Element  # type: ignore
from lxml.etree import _LogEntry  # type: ignore
from lxml.etree import (
    ParseError,
    XMLParser,
    XMLSchema,
    XMLSchemaParseError,
    XMLSyntaxError,
    parse,
)
from pydantic import BaseModel, ConfigDict, Field
from structlog.stdlib import get_logger

log = get_logger()


class SchemaCheckInputData(BaseModel):
    """
    Input data for the ETL Function
    """

    model_config = ConfigDict(populate_by_name=True)

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")


class TXCVersion(Enum):
    """Supported TransXChange schema versions."""

    V2_4 = "2.4"


def load_txc_schema(version: str = "2.4") -> XMLSchema:
    """
    Load the TransXChange XML schema for the specified version.
    """
    try:
        txc_version = TXCVersion(version)
    except ValueError:
        log.error(
            "Unsupported TXC Schema Version",
            version_provided=version,
            supported_versions=[v.value for v in TXCVersion],
        )
        raise

    schema_path = (
        Path(__file__).parent
        / "schema"
        / "txc"
        / txc_version.value
        / "TransXChange_general.xsd"
    )

    if not schema_path.exists():
        log.error("Schema File not Found", schema_path=str(schema_path))
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")
    log.info("Loading TXC Schema", schema_path=schema_path)
    try:
        parser = XMLParser(load_dtd=False, no_network=True)
        with open(schema_path, "rb") as schema_file:
            schema_doc = parse(schema_file, parser)
            log.debug("Parsed Schema Doc as _ElementTree[_Element]")
            txc_schema = XMLSchema(schema_doc)
            log.info("Sucessfully parsed Schema Doc as XMLSchema")
            return txc_schema
    except (XMLSchemaParseError, ParseError) as e:
        log.error("schema_parse_error", error=str(e))
        raise


def create_violation_from_error(
    error: _LogEntry, revision_id: int
) -> DataQualitySchemaViolation:
    """
    Create a DataQualitySchemaViolation instance from an lxml error
    """
    filename = Path(error.filename).name
    return DataQualitySchemaViolation(
        filename=filename,
        line=error.line,
        details=error.message,
        created=datetime.now(UTC),
        revision_id=revision_id,
    )


def get_schema_violations(
    txc_schema: XMLSchema, txc_file: _Element, revision_id: int
) -> list[DataQualitySchemaViolation]:
    """
    Validate parsed XML document against schema and collect any violations
    """
    violations: list[DataQualitySchemaViolation] = []
    log.info("Validating TXC File Against Schema")
    is_valid = txc_schema.validate(txc_file)

    if not is_valid:
        for error in txc_schema.error_log:
            violation = create_violation_from_error(error, revision_id)

            violations.append(violation)
    if violations:
        log.warning(
            "Schema Violations Found", count=len(violations), revision_id=revision_id
        )
    else:
        log.info("No Violations Found", revision_id=revision_id)
    return violations


def parse_xml_from_s3(input_data: SchemaCheckInputData) -> _Element:
    """
    Parse XML document from S3 object, streaming directly from S3 to lxml parser
    """
    s3_client = S3(bucket_name=input_data.s3_bucket_name)
    try:
        log.info("Downloading TXC XML from S3", s3_key=input_data.s3_file_key)
        streaming_body = s3_client.get_object(input_data.s3_file_key)
        txc_data = parse(streaming_body).getroot()
        log.info("Successfully Parsed TXC Data as LXML etree._Element")
        return txc_data
    except (ClientError, BotoCoreError) as e:
        log.error("S3 Operation Failed", s3_key=input_data.s3_file_key, error=str(e))
        raise
    except XMLSyntaxError as e:
        log.error("XML Parsing Failed", s3_key=input_data.s3_file_key, error=str(e))
        raise


def process_schema_check(
    input_data: SchemaCheckInputData,
) -> list[DataQualitySchemaViolation]:
    """
    Process Schema Check
    """
    txc_schema = load_txc_schema()
    txc_data = parse_xml_from_s3(input_data)

    return get_schema_violations(txc_schema, txc_data, input_data.revision_id)


def add_violations_to_db(
    db: SqlDB, violations: list[DataQualitySchemaViolation]
) -> list[DataQualitySchemaViolation]:
    """
    Add Schema Violations Found to Database
    """
    if len(violations) == 0:
        log.info("No Violations found. Skipping Database Insert of Violations")
        return []
    log.info("Adding Violations to DB", count=len(violations))
    result = DataQualitySchemaViolationRepo(db).bulk_insert(violations)
    log.info("Successfully added violations to DB", count=len(result))
    return result


class SchemaViolationsFound(Exception):
    """
    Exception raised when schema violation is found
    """


@file_processing_result_to_db(step_name=StepName.TIMETABLE_SCHEMA_CHECK)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Main lambda handler
    """
    input_data = SchemaCheckInputData(**event)
    db = SqlDB()

    try:
        violations = process_schema_check(input_data)

        if violations:
            add_violations_to_db(db, violations)
            raise SchemaViolationsFound(f"Found {len(violations)} Schema Violations")
    except Exception as e:
        log.error(
            "Error scanning file",
            bucket=input_data.s3_bucket_name,
            file_key=input_data.s3_file_key,
        )
        raise e
    return {
        "statusCode": 200,
        "body": f"Successfully ran the file schema check for file '{input_data.s3_file_key}' "
        f"from bucket '{input_data.s3_bucket_name}' with {len(violations)} violations",
    }
