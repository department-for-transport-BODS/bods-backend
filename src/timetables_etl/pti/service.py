from io import BytesIO

from botocore.response import StreamingBody
from common_layer.database.client import SqlDB
from common_layer.database.models.model_organisation import OrganisationDatasetRevision
from common_layer.db.repositories.pti_observation import PTIObservationRepository
from common_layer.dynamodb.client import DynamoDB
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.utils import sha1sum
from pti.validators.factory import get_xml_file_pti_validator
from pti.validators.txc_revision import TXCRevisionValidator
from structlog.stdlib import get_logger

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
            [
                live_attributes
                for live_attributes in live_revision_attributes
                if live_attributes.hash == file_hash
            ]
        )

    def validate(
        self,
        revision: OrganisationDatasetRevision,
        xml_file: BytesIO,
        txc_file_attributes: TXCFileAttributes,
    ):

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
            log.info(f"{len(violations)} violations found.")

            observation_repo = PTIObservationRepository(self._db)
            observation_repo.create(revision.id, violations)

        log.info("Finished PTI Profile validation.")
        return None
