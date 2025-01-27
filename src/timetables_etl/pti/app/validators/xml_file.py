"""
XML File PTI Validator
"""

from io import BytesIO
from typing import IO, Any

from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import NaptanStopPointDynamoDBClient
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.txc.models.txc_data import TXCData
from pti.app.pti_validation import DbClients
from structlog.stdlib import get_logger

from ..models.models_pti import PtiViolation
from .pti import PTIValidator

log = get_logger()


class XmlFilePTIValidator:
    """
    Run PTI validations against an XML File
    """

    def __init__(
        self,
        schema: IO[Any],
        db_clients: DbClients,
        txc_data: TXCData,
    ):
        self._validator = PTIValidator(schema, db_clients, txc_data)

    def get_violations(self, revision, xml_file_content: BytesIO) -> list[PtiViolation]:
        """
        Get any PTI violations for the given XML File.
        Will skip validation if the file exists in the live revision and is unchanged.
        """
        log.info(f"File for revision {revision.dataset_id} changed, validating...")

        self._validator.is_valid(xml_file_content)

        log.info(f"File for revision {revision.dataset_id} completed validation")
        log.info(f"File contains {len(self._validator.violations)} violations.")
        return self._validator.violations
