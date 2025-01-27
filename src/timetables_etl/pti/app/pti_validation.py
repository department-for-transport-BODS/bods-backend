"""
PtiValidation Lambda
"""

from io import BytesIO
from typing import Any

from attr import dataclass
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer import dynamodb
from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.database.repos import (
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.dynamodb.client import DynamoDB
from common_layer.dynamodb.client.cache import DynamoDBCache
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.dynamodb.data_manager import FileProcessingDataManager
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.s3 import S3
from common_layer.txc.models.txc_data import TXCData
from common_layer.txc.parser.parser_txc import (
    TXCParserConfig,
    load_xml_data,
    parse_txc_from_element,
)
from pydantic import BaseModel
from structlog.stdlib import get_logger

from .models import DbClients, PTITaskData
from .service import PTIValidationService

logger = get_logger()


class PTIValidationEvent(BaseModel):
    """
    Lambda Input Data
    """

    DatasetRevisionId: int
    Bucket: str
    ObjectKey: str
    TxcFileAttributesId: int


def get_xml_file(bucket: str, key: str) -> BytesIO:
    """
    Fetch and return BytesIO object for given S3 bucket/key
    """
    s3_handler = S3(bucket_name=bucket)
    s3_streaming_body = s3_handler.get_object(file_path=key)
    xml_file_object = BytesIO(s3_streaming_body.read())
    return xml_file_object


def get_txc_data(xml_file_object: BytesIO) -> TXCData:
    """
    Parse given xml_file_object to TXCData
    """
    parsed_xml = load_xml_data(xml_file_object)
    config = TXCParserConfig.parse_stops_only()
    txc_data = parse_txc_from_element(parsed_xml, config)
    return txc_data


def get_task_data(
    event: PTIValidationEvent, xml_file_object: BytesIO, clients: DbClients
) -> PTITaskData:
    """
    Fetch Required Task Data
    """
    dataset_revision_repo = OrganisationDatasetRevisionRepo(clients.sql_db)
    revision = dataset_revision_repo.get_by_id(event.DatasetRevisionId)
    if not revision:
        raise PipelineException(f"No revision with id {event.DatasetRevisionId} found")

    txc_file_attributes_repo = OrganisationTXCFileAttributesRepo(clients.sql_db)
    txc_file_attributes = txc_file_attributes_repo.get_by_id(event.TxcFileAttributesId)
    if not txc_file_attributes:
        message = (
            f"No TXCFileAttributes to process for DatasetRevision id {revision.id} "
        )
        logger.exception(message)
        raise PipelineException(message)

    data_manager = FileProcessingDataManager(clients.sql_db, clients.dynamodb)
    cached_live_txc_file_attributes = (
        data_manager.get_cached_live_txc_file_attributes(revision.id) or []
    )
    txc_data = get_txc_data(xml_file_object)

    return PTITaskData(
        revision=revision,
        txc_file_attributes=TXCFileAttributes.from_orm(txc_file_attributes),
        live_txc_file_attributes=cached_live_txc_file_attributes,
        xml_file_object=xml_file_object,
        txc_data=txc_data,
    )


def run_validation(task_data: PTITaskData, db_clients: DbClients):
    """
    Run PTI Validation
    """
    validation_service = PTIValidationService(
        db_clients, task_data.live_txc_file_attributes
    )
    validation_service.validate(
        task_data.revision,
        task_data.xml_file_object,
        task_data.txc_file_attributes,
        task_data.txc_data,
    )


@file_processing_result_to_db(step_name=StepName.PTI_VALIDATION)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    PTI Validation Lambda Entrypoint
    """
    parsed_event = PTIValidationEvent(**event)
    xml_file_object = get_xml_file(parsed_event.Bucket, parsed_event.ObjectKey)
    db_clients = DbClients(
        sql_db=SqlDB(),
        dynamodb=DynamoDBCache(),
        stop_point_client=NaptanStopPointDynamoDBClient(),
    )
    task_data = get_task_data(parsed_event, xml_file_object, db_clients)
    run_validation(task_data, db_clients)

    return {"statusCode": 200}
