"""
PTI Service
"""

from io import BytesIO

from common_layer.database.client import SqlDB
from common_layer.database.models.model_organisation import OrganisationDatasetRevision
from common_layer.database.repos.repo_data_quality import DataQualityPTIObservationRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationTXCFileAttributesRepo,
)
from common_layer.dynamodb.client import DynamoDB
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.utils import sha1sum
from structlog.stdlib import get_logger

from .models.models_pti import PtiViolation
from .validators.factory import get_xml_file_pti_validator
from .validators.txc_revision import TXCRevisionValidator

log = get_logger()


class PTIValidationService:
    """
    Class containing logic for PTI validation step
    """

    def __init__(
        self,
        db: SqlDB,
        dynamodb: DynamoDB,
        live_revision_attributes: list[TXCFileAttributes],
    ):
        self._db = db
        self._dynamodb = dynamodb
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
                f"File for revision {revision.dataset_id} unchanged, skipping PTI validation."
            )
        else:
            validator = get_xml_file_pti_validator(self._dynamodb, self._db)
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

                log.info(
                    "PTI Violation Found, Deleting TXC File Attribute Entry",
                    txc_file_attributes_id=txc_file_attributes.id,
                )
                txc_file_attribute_repo = OrganisationTXCFileAttributesRepo(self._db)
                txc_file_attribute_repo.delete_by_id(txc_file_attributes.id)

                raise ValueError("PTI validation failed due to violations")

        log.info("Finished PTI Profile validation.")
