"""
XML File PTI Validator
"""

from io import BytesIO
from typing import IO, Any

from common_layer.database.models import OrganisationDatasetRevision
from common_layer.xml.txc.models import TXCData
from structlog.stdlib import get_logger

from ..models import DbClients, PtiViolation
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

    def get_violations(
        self, revision: OrganisationDatasetRevision, xml_file_content: BytesIO
    ) -> list[PtiViolation]:
        """
        Get any PTI violations for the given XML File.
        Will skip validation if the file exists in the live revision and is unchanged.
        """
        log.info(
            "File for revision has changed. Revalidatiing.",
            organisation_dataset_id=revision.dataset_id,
            revision_id=revision.id,
        )

        self._validator.is_valid(xml_file_content)

        log.info(
            "File for revision completed validation",
            organisation_dataset_id=revision.dataset_id,
            revision_id=revision.id,
            violation_count=len(self._validator.violations),
        )
        return self._validator.violations
