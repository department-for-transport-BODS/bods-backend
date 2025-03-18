"""
Timetables ETL Statemachine Exception Handler
"""

from datetime import UTC, datetime
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.models import (
    DatasetETLTaskResult,
    ETLErrorCode,
    OrganisationDatasetRevision,
    TaskState,
)
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.enums import FeedStatus
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from .models import ExceptionHandlerInputData

log = get_logger()


def update_failure_state(
    task_result: DatasetETLTaskResult,
    error_message: str,
    error_code: ETLErrorCode = ETLErrorCode.SYSTEM_ERROR,
    step_name: str = "unknown",
) -> DatasetETLTaskResult:
    """
    Update task result with failure information
    Returns updated task result without saving to DB
    """
    if task_result.status == TaskState.FAILURE:
        return task_result

    task_result.status = TaskState.FAILURE
    task_result.completed = datetime.now(UTC)
    task_result.task_name_failed = step_name
    task_result.error_code = error_code
    task_result.additional_info = error_message

    return task_result


def save_changes(
    db: SqlDB, task_result: DatasetETLTaskResult, revision: OrganisationDatasetRevision
) -> None:
    """
    Save changes to both task result and revision
    """
    task_repo = ETLTaskResultRepo(db)
    revision_repo = OrganisationDatasetRevisionRepo(db)

    task_repo.update(task_result)
    revision_repo.update(revision)


def handle_error(
    db: SqlDB, event_data: ExceptionHandlerInputData
) -> tuple[DatasetETLTaskResult, OrganisationDatasetRevision]:
    """
    Core error handling logic
    """
    task_result = ETLTaskResultRepo(db).require_by_id(
        event_data.dataset_etl_task_result_id
    )

    revision = OrganisationDatasetRevisionRepo(db).require_by_id(
        task_result.revision_id
    )

    updated_task = update_failure_state(
        task_result,
        event_data.cause.extracted_message,
        error_code=event_data.cause.error_code,
    )

    if updated_task.status == TaskState.FAILURE:
        revision.status = FeedStatus.ERROR
        save_changes(db, updated_task, revision)

    return updated_task, revision


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Timetables ETL Statemachine Exception Handler
    """
    log.info("Exception Event", data=event)
    configure_logging(event, context)

    parsed_event = ExceptionHandlerInputData(**event)
    log.error(
        parsed_event.cause.error_message,
        error_details=parsed_event.cause,
    )

    db = SqlDB()
    task_result, revision = handle_error(db, parsed_event)

    return {
        "statusCode": 200,
        "revision_id": revision.id,
        "task_result_id": task_result.id,
    }
