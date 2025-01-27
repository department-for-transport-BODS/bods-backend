"""
PTI Service
"""

from io import BytesIO

from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.database.repos import (
    DataQualityPTIObservationRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.txc.models.txc_data import TXCData
from common_layer.utils import sha1sum
from pti.app.pti_validation import DbClients
from structlog.stdlib import get_logger

from .models.models_pti import PtiViolation
from .validators.factory import get_xml_file_pti_validator
from .validators.txc_revision import TXCRevisionValidator

log = get_logger()


def get_unique_violation_names(violations: list[PtiViolation]) -> list[str]:
    """
    Create a list of unique violations for logging
    """
    return list(set(v.name for v in violations))


class PTIValidationService:
    """
    Class containing logic for PTI validation step
    """

    def __init__(
        self,
        db_clients: DbClients,
        live_revision_attributes: list[TXCFileAttributes],
    ):
        self._db_clients = db_clients
        self._live_revision_attributes = live_revision_attributes

    def is_file_unchanged(
        self,
        file_hash: str,
        live_revision_attributes: list[TXCFileAttributes],
    ) -> bool:
        """
        Checks if the given file hash already exists in the live revision
        """
        return any(
            live_attributes
            for live_attributes in live_revision_attributes
            if live_attributes.hash == file_hash
        )

    def validate(
        self,
        revision: OrganisationDatasetRevision,
        xml_file: BytesIO,
        txc_file_attributes: TXCFileAttributes,
        txc_data: TXCData,
    ):
        """
        Run PTI validation against the given revision and file
        """

        log.info("Starting PTI Profile validation.")

        file_content_bytes = xml_file.read()
        file_hash = sha1sum(file_content_bytes)
        xml_file.seek(0)

        if self.is_file_unchanged(file_hash, self._live_revision_attributes):
            log.info(
                "File for revision unchanged, skipping PTI validation.",
                revision_id=revision.dataset_id,
            )
        else:
            validator = get_xml_file_pti_validator(
                self._dynamodb, self._stop_point_client, self._db, txc_data
            )
            violations = validator.get_violations(revision, xml_file)

            revision_validator = TXCRevisionValidator(
                txc_file_attributes, self._live_revision_attributes
            )
            violations += revision_validator.get_violations()

            if violations:
                log.info("Violations found", count=len(violations))
                observations = [
                    PtiViolation.make_observation(revision.id, violation)
                    for violation in violations
                ]
                observation_repo = DataQualityPTIObservationRepo(self._db)
                observation_repo.bulk_insert(observations)
                unique_names = get_unique_violation_names(violations)
                log.info(
                    "PTI Violation Found, Deleting TXC File Attribute Entry",
                    txc_file_attributes_id=txc_file_attributes.id,
                    violations=unique_names,
                )
                txc_file_attribute_repo = OrganisationTXCFileAttributesRepo(self._db)
                txc_file_attribute_repo.delete_by_id(txc_file_attributes.id)

                raise ValueError(
                    f"PTI validation failed due to violations. {','.join(unique_names)}"
                )
        log.info("Finished PTI Profile validation.")
