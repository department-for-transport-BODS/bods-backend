from common_layer.db.manager import DbManager
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.db.repositories.dataset_revision import DatasetRevisionRepository
from common_layer.db.repositories.txc_file_attributes import TxcFileAttributesRepository
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.logger import get_dataset_adapter_from_revision
from pti.service import PTIValidationService
from pydantic import BaseModel
from common_layer.s3 import S3


class PTIValidationEvent(BaseModel):
    DatasetRevisionId: int
    Bucket: str
    ObjectKey: str


@file_processing_result_to_db(step_name=StepName.PTI_VALIDATION)
def lambda_handler(event, context):
    parsed_event = PTIValidationEvent(**event)

    db = DbManager.get_db()

    dataset_revision_repo = DatasetRevisionRepository(db)
    revision = dataset_revision_repo.get_by_id(parsed_event.DatasetRevisionId)

    adapter = get_dataset_adapter_from_revision(revision.id, revision.dataset_id)

    s3_handler = S3(bucket_name=parsed_event.Bucket)
    filename = parsed_event.ObjectKey
    xml_file_object = s3_handler.get_object(file_path=filename)

    txc_file_attributes_repo = TxcFileAttributesRepository(db)
    txc_file_attributes = txc_file_attributes_repo.get(revision_id=revision.id, filename=filename)
    if not txc_file_attributes:
        message = f"Validation task: pti_validation, no valid file to process, zip file: {revision.upload_file}"
        adapter.error(message, exc_info=True)
        raise PipelineException(message)

    validation_service = PTIValidationService(db)
    validation_service.validate(revision, xml_file_object, txc_file_attributes)

    return {"statusCode": 200}
