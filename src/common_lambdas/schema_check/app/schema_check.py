"""
SchemaCheckLambda
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import BotoCoreError, ClientError
from common_layer.database.client import SqlDB
from common_layer.database.models.model_data_quality import DataQualitySchemaViolation
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from common_layer.s3.utils import get_filename_from_object_key
from lxml.etree import _Element  # type: ignore
from lxml.etree import XMLSchema, XMLSyntaxError, parse
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings
from structlog.stdlib import get_logger

from .constants import XMLDataType, XMLSchemaType
from .db_operations import add_violations_to_db, create_violation_from_error
from .schema_loader import load_schema
from .utils import get_xml_type

log = get_logger()


class SchemaCheckSettings(BaseSettings):
    """
    Configure schema check for FARES or TIMETABLES

    TODO: Replace this with a field in SchemaCheckInputData
    once Schema Check lambda is promoted to its own application
    """

    XML_DATA_TYPE: XMLDataType | None = Field(
        default=None, description="Type of check: FARES or TIMETABLES"
    )


class SchemaCheckInputData(BaseModel):
    """
    Input data for the Schema Check Function
    """

    model_config = ConfigDict(populate_by_name=True)

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")
    data_type: XMLDataType = Field(alias="DataType")


def get_schema_violations(
    txc_schema: XMLSchema,
    txc_file: _Element,
    revision_id: int,
    filename: str,
) -> list[DataQualitySchemaViolation]:
    """
    Validate parsed XML document against schema and collect any violations
    """
    violations: list[DataQualitySchemaViolation] = []
    log.info("Validating TXC File Against Schema")
    is_valid = txc_schema.validate(txc_file)

    if not is_valid:
        for error in txc_schema.error_log:
            violation = create_violation_from_error(error, revision_id, filename)
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
        log.info("Successfully Parsed TXC Data as LXML _Element")
        return txc_data
    except (ClientError, BotoCoreError):
        log.error("S3 Operation Failed", s3_key=input_data.s3_file_key, exc_info=True)
        raise
    except XMLSyntaxError:
        log.error("XML Parsing Failed", s3_key=input_data.s3_file_key, exc_info=True)
        raise


def validate_schema_type(data_type: XMLDataType, detected_schema_type: XMLSchemaType):
    """
    Validate that the detected XMLSchemaType based on the expected XMLDataType.

    If the detected schema type does not match the expected type, an exception is raised.
    """
    expected_mapping = {
        XMLDataType.TIMETABLES: XMLSchemaType.TRANSXCHANGE,
        XMLDataType.FARES: XMLSchemaType.NETEX,
    }

    expected_schema_type = expected_mapping.get(data_type)
    if expected_schema_type is None:
        raise ValueError(f"XML_DATA_TYPE '{data_type}' not found in mapping")

    if detected_schema_type != expected_schema_type:
        msg = "XMLSchemaType mismatch: provided XML file does not match expected schema type"
        log.error(
            msg,
            exected_schema_type=expected_schema_type,
            detected_schema_type=detected_schema_type,
        )
        raise ValueError(msg)


def process_schema_check(
    input_data: SchemaCheckInputData,
) -> list[DataQualitySchemaViolation]:
    """
    Process Schema Check
    """
    xml_root = parse_xml_from_s3(input_data)
    schema_type, schema_version = get_xml_type(xml_root)

    # TODO: Replace SchemaCheckSettings with input_data.XML_DATA_TYPE # pylint: disable=fixme
    # once Lambda is promoted to its own application
    settings = SchemaCheckSettings()
    if settings.XML_DATA_TYPE is None:
        msg = "Expected XML_DATA_TYPE is not set in environment variables."
        log.error(msg)
        raise ValueError(msg)
    validate_schema_type(settings.XML_DATA_TYPE, schema_type)

    xml_schema = load_schema(schema_type, schema_version)

    filename = get_filename_from_object_key(input_data.s3_file_key)
    if not filename:
        raise ValueError(
            f"Unable to parse filename from input_data.s3_file_key: {input_data.s3_file_key}"
        )

    return get_schema_violations(xml_schema, xml_root, input_data.revision_id, filename)


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
