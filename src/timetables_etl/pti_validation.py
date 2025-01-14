"""
PtiValidation Lambda
"""

from io import BytesIO

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.models.model_organisation import OrganisationDatasetRevision
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.dynamodb.client import DynamoDB
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.s3 import S3
from pti.service import PTIValidationService
from pydantic import BaseModel, ConfigDict
from structlog.stdlib import get_logger

tracer = Tracer()
logger = get_logger()


class PTIValidationEvent(BaseModel):
    """
    Lambda Input Data
    """

    DatasetRevisionId: int
    Bucket: str
    ObjectKey: str
    TxcFileAttributesId: int


class PTITaskData(BaseModel):
    """
    Task Data Container
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    revision: OrganisationDatasetRevision
    txc_file_attributes: TXCFileAttributes
    live_txc_file_attributes: list[TXCFileAttributes]
    xml_file_object: BytesIO


def get_xml_file(bucket: str, key: str) -> BytesIO:
    s3_handler = S3(bucket_name=bucket)
    s3_streaming_body = s3_handler.get_object(file_path=key)
    xml_file_object = BytesIO(s3_streaming_body.read())
    return xml_file_object


def get_task_data(
    event: PTIValidationEvent, xml_file_object: BytesIO, db: SqlDB, dynamodb: DynamoDB
) -> PTITaskData:
    """
    Fetch Required Task Data
    """
    dataset_revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = dataset_revision_repo.get_by_id(event.DatasetRevisionId)
    if not revision:
        raise PipelineException(f"No revision with id {event.DatasetRevisionId} found")

    txc_file_attributes_repo = OrganisationTXCFileAttributesRepo(db)
    txc_file_attributes = txc_file_attributes_repo.get_by_id(event.TxcFileAttributesId)
    if not txc_file_attributes:
        message = (
            f"No TXCFileAttributes to process for DatasetRevision id {revision.id} "
        )
        logger.exception(message)
        raise PipelineException(message)

    data_manager = FileProcessingDataManager(db, dynamodb)
    cached_live_txc_file_attributes = (
        data_manager.get_cached_live_txc_file_attributes(revision.id) or []
    )

    return PTITaskData(
        revision=revision,
        txc_file_attributes=TXCFileAttributes.from_orm(txc_file_attributes),
        live_txc_file_attributes=cached_live_txc_file_attributes,
        xml_file_object=xml_file_object,
    )


def run_validation(task_data: PTITaskData, db: SqlDB, dynamodb: DynamoDB):
    """
    Run PTI Validation
    """
    validation_service = PTIValidationService(
        db, dynamodb, task_data.live_txc_file_attributes
    )
    validation_service.validate(
        task_data.revision, task_data.xml_file_object, task_data.txc_file_attributes
    )


@tracer.capture_lambda_handler
@file_processing_result_to_db(step_name=StepName.PTI_VALIDATION)
def lambda_handler(event, _context: LambdaContext):
    """
    PTI Validation Lambda Entrypoint
    """
    parsed_event = PTIValidationEvent(**event)
    db = SqlDB()
    dynamodb = DynamoDB()
    xml_file_object = get_xml_file(parsed_event.Bucket, parsed_event.ObjectKey)
    task_data = get_task_data(parsed_event, xml_file_object, db, dynamodb)
    run_validation(task_data, db, dynamodb)

    return {"statusCode": 200}
