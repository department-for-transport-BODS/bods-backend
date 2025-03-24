"""
Timetables ETL Statemachine Exception Handler
"""

from typing import Any

import common_layer.aws.datadog.tracing  # type: ignore # pylint: disable=unused-import
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.enums import FeedStatus
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from .models import ExceptionHandlerInputData

log = get_logger()


def handle_error(
    db: SqlDB, event_data: ExceptionHandlerInputData
) -> OrganisationDatasetRevision:
    """
    Core error handling logic
    """
    task_result = ETLTaskResultRepo(db).require_by_id(
        event_data.dataset_etl_task_result_id
    )

    revision = OrganisationDatasetRevisionRepo(db).require_by_id(
        task_result.revision_id
    )

    ETLTaskResultRepo(db).mark_error(
        task_id=event_data.dataset_etl_task_result_id,
        task_name="Exception Handler Does not Know Failed Task Name",
        error_code=event_data.cause.error_code,
        additional_info=event_data.cause.extracted_message,
    )
    revision.status = FeedStatus.ERROR
    OrganisationDatasetRevisionRepo(db).update(revision)

    return revision


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
