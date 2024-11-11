from os import environ
from pydantic import BaseModel
from common import LambdaEvent
from datetime import datetime
from db.dataset_etl_task_result import DatasetETLTaskResultRepository
from db.dataset_revision import DatasetRevisionRepository
from enums import DatasetETLResultStatus
from logger import get_dataset_adapter_from_revision, logger
import json


class ErrorInfo(BaseModel):
    error_message: str
    step_name: str


class ExceptionEvent(BaseModel):
    DatasetEtlTaskResultId: int
    ErrorInfo: ErrorInfo


def lambda_handler(event, context):
    parsed_event = ExceptionEvent(**event)
    lambda_event = LambdaEvent(event)

    taskResultRepo = DatasetETLTaskResultRepository(lambda_event.db)
    datasetETLResult = taskResultRepo.get_by_id(parsed_event.DatasetEtlTaskResultId)

    revisionRepo = DatasetRevisionRepository(lambda_event.db)
    revision = revisionRepo.get_by_id(datasetETLResult.revision_id)
    adapter = get_dataset_adapter_from_revision(revision.id, revision.dataset_id)
    adapter.error(parsed_event.ErrorInfo.error_message, exc_info=True)

    if datasetETLResult.status != DatasetETLResultStatus.FAILURE:
        datasetETLResult.status = DatasetETLResultStatus.FAILURE
        datasetETLResult.completed = datetime.now()
        datasetETLResult.task_name_failed = parsed_event.ErrorInfo.step_name
        datasetETLResult.error_code = DatasetETLResultStatus.SYSTEM_ERROR
        datasetETLResult.additional_info = parsed_event.ErrorInfo.error_message

        taskResultRepo.update(datasetETLResult)

    # TODO: Set revivision to error

    return
