from io import BytesIO
from typing import IO, Any, List

from botocore.response import StreamingBody
from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import DynamoDB
from common_layer.pti.models import Violation
from pti.validators.pti import PTIValidator
from structlog.stdlib import get_logger

log = get_logger()


class XmlFilePTIValidator:
    def __init__(self, schema: IO[Any], dynamodb: DynamoDB, db: SqlDB):
        self._validator = PTIValidator(schema, dynamodb, db)

    def get_violations(self, revision, xml_file: StreamingBody) -> List[Violation]:
        """
        Get any PTI violations for the given XML File.
        Will skip validation if the file exists in the live revision and is unchanged.
        """
        log.info(f"File for revision {revision.dataset_id} changed, validating...")

        file_content = xml_file.read()
        self._validator.is_valid(BytesIO(file_content))

        log.info(f"File for revision {revision.dataset_id} completed validation")
        log.info(f"File contains {len(self._validator.violations)} violations.")
        return self._validator.violations
