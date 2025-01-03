from io import BytesIO
from logging import getLogger
from typing import IO, Any, List

from botocore.response import StreamingBody
from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import DynamoDB
from common_layer.logger import get_dataset_adapter_from_revision
from common_layer.pti.models import Violation
from pti.validators.pti import PTIValidator

logger = getLogger(__name__)


class XmlFilePTIValidator:
    def __init__(self, schema: IO[Any], dynamodb: DynamoDB, db: SqlDB):
        self._validator = PTIValidator(schema, dynamodb, db)

    def get_violations(self, revision, xml_file: StreamingBody) -> List[Violation]:
        """
        Get any PTI violations for the given XML File.
        Will skip validation if the file exists in the live revision and is unchanged.
        """
        adapter = get_dataset_adapter_from_revision(revision.id, revision.dataset_id)
        adapter.info(f"File for revision {revision.dataset_id} changed, validating...")

        file_content = xml_file.read()
        self._validator.is_valid(BytesIO(file_content))

        adapter.info(f"File for revision {revision.dataset_id} completed validation")
        adapter.info(f"File contains {len(self._validator.violations)} violations.")
        return self._validator.violations
