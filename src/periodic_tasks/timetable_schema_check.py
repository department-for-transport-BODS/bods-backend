import os
import json
from pathlib import Path
from logger import logger
from s3 import S3
from zipfile import ZipFile
from lxml import etree

from db.file_processing_result import file_processing_result_to_db
from db.dataset_revision import get_dataset_revision
from db.schema_definition import get_schema_definition_db_object
from constants import SCHEMA_DIR
from violations import BaseSchemaViolation
from xml_validator import XMLValidator
from db.schema_violation import SchemaViolation
from common import LambdaEvent


def get_transxchange_schema():
    definition = get_schema_definition_db_object()
    schema_loader = SchemaLoader(definition, os.environ["TXC_XSD_PATH"])
    return schema_loader.schema


class SchemaLoader:
    """
    Class for unzipping xsd schemas onto local filesystem
    """

    def __init__(self, definition, xsd_path: str):
        self.definition = definition
        self._path = xsd_path
        self._schema_dir: str = SCHEMA_DIR

    @property
    def path(self) -> Path:
        """
        Returns path of main XSD file for use in schema validation.
        If the path doesnt exist in the local filesystem it is re acquired
        """
        directory = Path(self._schema_dir) / self.definition.category
        if not directory.exists():
            directory.mkdir(parents=True)
            logger.info(f"Directory {directory} created")

        path = directory / self._path

        if not path.exists():
            with ZipFile(self.definition.schema) as zin:
                for filepath in zin.namelist():
                    # Not sure why this is necessary but the netex zip triggers
                    # zip bomb warning and a couple of examples cant be extracted
                    # This is probably fine because these are known zip files from
                    # DfT
                    try:
                        zin.extract(filepath, directory)
                    except (OSError, ValueError) as e:
                        logger.warning(f"Could not extract {filepath} - {e}")
                        # We probably want to fail the pipeline if there are any other
                        # exceptions

        return path

    @property
    def schema(self) -> etree.XMLSchema:
        """
        Return a complete XSD XMLSchema object
        """
        with self.path.open("r") as f:
            doc = etree.parse(f)
            return etree.XMLSchema(doc)


class DatasetTXCValidator:
    def __init__(self, revision):
        self._schema = get_transxchange_schema()
        self.revision = revision

    def get_violations(self, file_):
        violations = []
        error = XMLValidator(file_).dangerous_xml_check()
        if error:
            file_.seek(0)
            violations.append(
                BaseSchemaViolation.from_error(error[0], revision_id=self.revision.id)
            )
            return violations
        file_.seek(0)
        doc = etree.parse(file_)
        is_valid = self._schema.validate(doc)
        if not is_valid:
            for error in self._schema.error_log:
                violations.append(
                    BaseSchemaViolation.from_error(error, revision_id=self.revision.id)
                )
        return violations


@file_processing_result_to_db(step_name="Timetable Schema Check")
def lambda_handler(event, context):
    """
    Main lambda handler
    """
    logger.info(f"Received event:{json.dumps(event, indent=2)}")

    # Extract the bucket name and object key from the S3 event
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    filename = key.split("/")[-1]
    revision_id = key.split("/")[0]

    revision = get_dataset_revision(revision_id=revision_id)
    # URL-decode the key if it has special characters
    filename = filename.replace("+", " ")
    try:
        s3_handler = S3(bucket_name=bucket)
        file_object = s3_handler.get_object(file_path=filename)
        validator = DatasetTXCValidator(revision=revision)
        violations = validator.get_violations(file_object)
        lambda_event = LambdaEvent(event)
        schema_violation = SchemaViolation(lambda_event.db)
        schema_violation.create(violations)
    except Exception as e:
        logger.error(f"Error scanning object '{key}' from bucket '{bucket}'")
        raise e
    return {
        "statusCode": 200,
        "body": f"Successfully ran the file schema check for file '{key}' from bucket '{bucket}' with {len(violations)} violations",
    }
