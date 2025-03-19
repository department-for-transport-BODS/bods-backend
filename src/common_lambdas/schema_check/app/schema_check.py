"""
SchemaCheckLambda
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import BotoCoreError, ClientError
from common_layer.database.client import SqlDB
from common_layer.database.models import DataQualitySchemaViolation
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.exceptions import SchemaMismatch, SchemaUnknown, SchemaViolationsFound
from common_layer.exceptions import XMLSyntaxError as ETLXMLSyntaxError
from common_layer.s3 import S3, get_filename_from_object_key_except
from lxml.etree import _Element  # type: ignore
from lxml.etree import XMLSchema, XMLSyntaxError, parse
from pydantic import BaseModel, ConfigDict, Field
from structlog.stdlib import get_logger

from .constants import XMLDataType, XMLSchemaType
from .db_operations import add_violations_to_db, create_violation_from_error
from .schema_loader import load_schema
from .utils import get_xml_type

log = get_logger()


class SchemaCheckInputData(BaseModel):
    """
    Input data for the Schema Check Function
    """

    model_config = ConfigDict(populate_by_name=True)

    revision_id: int = Field(alias="DatasetRevisionId")
    s3_bucket_name: str = Field(alias="Bucket")
    s3_file_key: str = Field(alias="ObjectKey")
    dataset_type: XMLDataType = Field(
        default=XMLDataType.TIMETABLES, alias="DatasetType"
    )


def get_schema_violations(
    schema: XMLSchema,
    file: _Element,
    revision_id: int,
    filename: str,
) -> list[DataQualitySchemaViolation]:
    """
    Validate parsed XML document against schema and collect any violations
    """
    violations: list[DataQualitySchemaViolation] = []
    log.info("Validating File Against Schema")
    is_valid = schema.validate(file)

    if not is_valid:
        for error in schema.error_log:
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
        log.info("Downloading XML from S3", s3_key=input_data.s3_file_key)
        streaming_body = s3_client.get_object(input_data.s3_file_key)
        data = parse(streaming_body).getroot()
        log.info("Successfully Parsed Data as LXML _Element")
        return data
    except (ClientError, BotoCoreError):
        log.error("S3 Operation Failed", s3_key=input_data.s3_file_key, exc_info=True)
        raise
    except XMLSyntaxError as exc:
        log.error("XML Parsing Failed", s3_key=input_data.s3_file_key, exc_info=True)
        raise ETLXMLSyntaxError from exc


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
        raise SchemaUnknown(input_data_type=data_type)

    if detected_schema_type != expected_schema_type:
        log.error(
            "XMLSchemaType mismatch: provided XML file does not match expected schema type",
            exected_schema_type=expected_schema_type,
            detected_schema_type=detected_schema_type,
        )
        raise SchemaMismatch(
            detected_schema_type=detected_schema_type,
            expected_schema_type=expected_schema_type,
        )


def process_schema_check(
    input_data: SchemaCheckInputData,
) -> list[DataQualitySchemaViolation]:
    """
    Process Schema Check
    """
    xml_root = parse_xml_from_s3(input_data)
    schema_type, schema_version = get_xml_type(xml_root)

    validate_schema_type(input_data.dataset_type, schema_type)

    xml_schema = load_schema(schema_type, schema_version)

    filename = get_filename_from_object_key_except(input_data.s3_file_key)

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
            raise SchemaViolationsFound(violations=len(violations))
    except Exception as e:
        log.error(
            "Error scanning file",
            bucket=input_data.s3_bucket_name,
            file_key=input_data.s3_file_key,
        )
        raise e
    return {
        "statusCode": 200,
        "message": "Successfully ran the file schema check for file",
        "ObjectKey": input_data.s3_file_key,
        "Bucket": input_data.s3_bucket_name,
        "violations": len(violations),
    }
