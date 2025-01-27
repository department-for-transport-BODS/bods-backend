"""
DQS Trigger Lambda
"""

from io import BytesIO
from os import environ

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_dqs import DQSChecksRepo, DQSReportRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo, OrganisationTXCFileAttributesRepo)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.exceptions.pipeline_exceptions import PipelineException
from dqs.step_function_client import StepFunctionsClientWrapper
from pydantic import BaseModel
from structlog.stdlib import get_logger

tracer = Tracer()
logger = get_logger()


class DQSTriggerEvent(BaseModel):
    """
    Lambda Input Data
    """

    DatasetRevisionId: int

def get_org_revision(revision_id: int, db: SqlDB) -> BytesIO:
    """
    Retrieves the org dataset revision object for the revision_id
    """
    dataset_revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = dataset_revision_repo.get_by_id(revision_id)
    if not revision:
        raise PipelineException(f"No revision with id {revision_id} found")
    return revision


def initialise_dqs_report(revision_id: int, revision: object, db: SqlDB) -> None:
    """
    Updates the dqs_report table for the revision_id
    """
    dqs_report_repo = DQSReportRepo(db)
    dqs_report = dqs_report_repo.get_by_revision_id(revision_id)

    if dqs_report:
        dqs_report_repo.delete_report_by_revision_id(revision_id)
    
    dqs_report_repo.create_report_for_revision(revision)

def get_txc_file_attributes(revision_id: int, db: SqlDB) -> list:
    """
    Get all organisation_txcfileattributes objects
    """
    org_txcfileattributes_repo = OrganisationTXCFileAttributesRepo(db)
    org_txcfileattributes = org_txcfileattributes_repo.get_by_revision_id(revision_id)

    return org_txcfileattributes

def run_dqs_trigger(txc_file_attributes):
    """
    Invoke the step machine execution
    """
    step_function_client = StepFunctionsClientWrapper()
    for file in txc_file_attributes:
        execution_arn = step_function_client.start_execution(
            state_machine_arn=environ.get("STATE_MACHINE_ARN", default=""),
            input=dict(file_id=file.id),
            name=f"DQSExecutionForRevision{file.id}",
        )
        logger.info(
            f"Began State Machine Execution for {file.id}: {execution_arn}"
        )

@tracer.capture_lambda_handler
@file_processing_result_to_db(step_name=StepName.DQS_TRIGGER)
def lambda_handler(event, _context: LambdaContext):
    """
    DQS Trigger Lambda Entrypoint
    """
    event ={"DatasetRevisionId":442}
    parsed_event = DQSTriggerEvent(**event)
    db = SqlDB()
    org_revision_object = get_org_revision(parsed_event.DatasetRevisionId, db)
    initialise_dqs_report(parsed_event.DatasetRevisionId, org_revision_object, db)
    txc_file_attributes = get_txc_file_attributes(parsed_event.DatasetRevisionId, db)
    run_dqs_trigger(txc_file_attributes)

    return {"statusCode": 200}
