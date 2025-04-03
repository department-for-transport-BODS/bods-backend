"""
Timetables ETL Statemachine Exception Handler
"""

from typing import Any

import common_layer.aws.datadog.tracing  # type: ignore # pylint: disable=unused-import
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.enums import FeedStatus
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from .models import ExceptionHandlerInputData

log = get_logger()


def handle_error(db: SqlDB, event_data: ExceptionHandlerInputData):
    """
    Core error handling logic
    """
    task_result_repo = ETLTaskResultRepo(db)
    task_result = task_result_repo.require_by_id(event_data.dataset_etl_task_result_id)

    if event_data.fail_dataset_etl_task_result:
        task_result_repo.mark_error(
            task_id=event_data.dataset_etl_task_result_id,
            task_name=event_data.step_name,
            error_code=event_data.cause.error_code,
            additional_info=event_data.cause.extracted_message,
        )

    if event_data.fail_dataset_revision:
        revision_repo = OrganisationDatasetRevisionRepo(db)
        revision = revision_repo.require_by_id(task_result.revision_id)
        revision.status = FeedStatus.ERROR
        revision_repo.update(revision)


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
    handle_error(db, parsed_event)

    return {
        "statusCode": 200,
    }
