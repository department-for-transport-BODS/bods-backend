from botocore.response import StreamingBody
from common_layer.dynamodb.client import DynamoDB
from common_layer.utils import sha1sum
from common_layer.db import BodsDB
from common_layer.db.models import (
    OrganisationDatasetrevision,
    OrganisationTxcfileattributes,
)
from common_layer.db.repositories.dataset import DatasetRepository
from common_layer.db.repositories.pti_observation import PTIObservationRepository
from common_layer.db.repositories.txc_file_attributes import TxcFileAttributesRepository
from common_layer.logger import PipelineAdapter, get_dataset_adapter_from_revision
from pti.validators.factory import get_xml_file_pti_validator
from pti.validators.txc_revision import TXCRevisionValidator


class PTIValidationService:
    """
    Class containing logic for PTI validation step
    """

    def __init__(self, db: BodsDB, dynamodb: DynamoDB):
        self.db = db
        self.dynamodb = dynamodb

    def is_file_unchanged(
        self, dataset_id: int, file_hash: str, adapter: PipelineAdapter
    ) -> bool:
        """
        Checks if the given file hash already exists in the live revision for the given dataset_id
        """
        try:
            dataset_repo = DatasetRepository(self.db)
            dataset = dataset_repo.get_by_id(dataset_id)

            txc_file_attributes_repo = TxcFileAttributesRepository(self.db)
            return txc_file_attributes_repo.exists(
                revision_id=dataset.live_revision_id, hash=file_hash
            )
        except Exception as e:
            adapter.error(f"Error checking if file is unchanged: {e}")
            return False

    def validate(
        self,
        revision: OrganisationDatasetrevision,
        xml_file: StreamingBody,
        txc_file_attributes: OrganisationTxcfileattributes,
    ):
        adapter = get_dataset_adapter_from_revision(revision.id, revision.dataset_id)

        adapter.info("Starting PTI Profile validation.")

        file_content = xml_file.read()
        file_hash = sha1sum(file_content)

        if self.is_file_unchanged(revision.dataset_id, file_hash, adapter):
            adapter.info(
                f"File for revision {revision.dataset_id} unchanged, skipping PTI validation."
            )
        else:
            validator = get_xml_file_pti_validator(self.dynamodb)
            violations = validator.get_violations(revision, xml_file)

            revision_validator = TXCRevisionValidator(revision, txc_file_attributes)
            violations += revision_validator.get_violations()
            adapter.info(f"{len(violations)} violations found.")

            observation_repo = PTIObservationRepository(self.db)
            observation_repo.create(revision.id, violations)

        adapter.info("Finished PTI Profile validation.")
        return None
