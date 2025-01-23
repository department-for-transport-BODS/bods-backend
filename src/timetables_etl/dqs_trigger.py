"""
PtiValidation Lambda
"""

from io import BytesIO

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_dqs import DQSChecksRepo, DQSReportRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo, OrganisationTXCFileAttributesRepo)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.exceptions.pipeline_exceptions import PipelineException
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
    Updates the dqs_report table for the revision_id
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
    

def get_all_checks(db: SqlDB) -> object:
    """
    Get all dqs_checks objects
    """
    dqs_checks_repo = DQSChecksRepo(db)
    dqs_checks = dqs_checks_repo.get_all_checks()

    return dqs_checks

def get_txc_file_attributes(revision_id: int, db: SqlDB) -> object:
    """
    Get all dqs_checks objects
    """
    org_txcfileattributes_repo = OrganisationTXCFileAttributesRepo(db)
    org_txcfileattributes = org_txcfileattributes_repo.get_by_revision_id(revision_id)

    return org_txcfileattributes

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
    dqs_checks = get_all_checks(db)
    txc_file_attributes_objects = get_txc_file_attributes(parsed_event.DatasetRevisionId, db)

    return {"statusCode": 200}
