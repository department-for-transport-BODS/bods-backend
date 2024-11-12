from pydantic import BaseModel
from common import LambdaEvent
from datetime import datetime
from db.dataset_etl_task_result import DatasetETLTaskResultRepository
from db.dataset_revision import DatasetRevisionRepository
from enums import DatasetETLResultStatus, FeedStatus
from logger import get_dataset_adapter_from_revision


class ErrorInfo(BaseModel):
    error_message: str
    step_name: str


class ExceptionEvent(BaseModel):
    DatasetEtlTaskResultId: int
    ErrorInfo: ErrorInfo


def lambda_handler(event, context):
    parsed_event = ExceptionEvent(**event)
    lambda_event = LambdaEvent(event)

    task_result_repo = DatasetETLTaskResultRepository(lambda_event.db)
    dataset_etl_task_result = task_result_repo.get_by_id(parsed_event.DatasetEtlTaskResultId)

    dataset_revision_repo = DatasetRevisionRepository(lambda_event.db)
    revision = dataset_revision_repo.get_by_id(dataset_etl_task_result.revision_id)

    adapter = get_dataset_adapter_from_revision(revision.id, revision.dataset_id)
    error_message = parsed_event.ErrorInfo.error_message
    adapter.error(error_message, exc_info=True)

    if dataset_etl_task_result.status != DatasetETLResultStatus.FAILURE:
        dataset_etl_task_result.status = DatasetETLResultStatus.FAILURE
        dataset_etl_task_result.completed = datetime.now()
        dataset_etl_task_result.task_name_failed = parsed_event.ErrorInfo.step_name
        dataset_etl_task_result.error_code = DatasetETLResultStatus.SYSTEM_ERROR
        dataset_etl_task_result.additional_info = error_message
        task_result_repo.update(dataset_etl_task_result)

        revision.status = FeedStatus.error
        dataset_revision_repo.update(revision)

    return {
        "statusCode": 200
    }
