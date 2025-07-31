"""
Timetables ETL Statemachine Exception Handler
"""

from os import environ
from typing import Any

import common_layer.aws.datadog.tracing  # type: ignore # pylint: disable=unused-import
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database.client import SqlDB
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationOrganisationRepo,
    UsersUserRepo,
)
from common_layer.enums import FeedStatus
from common_layer.json_logging import configure_logging
from common_layer.notification import get_notifications
from structlog.stdlib import get_logger

from .models import ExceptionHandlerInputData

log = get_logger()

EMAIL_STEPS = ["File Validation"]
AGENT_USER = 5
DATASET_TIMETABLE = 1
DATASET_FARES = 3


def send_failure_email(db: SqlDB, revision_id: int):
    """Send the failure email

    Args:
        db (SqlDB): db object to find all the necessary details
        event_data (ExceptionHandlerInputData): Event data object with all the information
    """
    log.info("Sending the email for the failure", revision_id=revision_id)
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = revision_repo.require_by_id(revision_id)

    dataset_repo = OrganisationDatasetRepo(db)
    dataset = dataset_repo.get_by_id(revision.dataset_id)

    user_repo = UsersUserRepo(db)
    modified_by = user_repo.require_by_id(revision.last_modified_user_id)

    base_url = environ.get("FRONTEND_BASE_URL", "bus-data.dft.gov.uk")
    dataset_page_path = (
        f"org/{dataset.organisation_id}/dataset/timetable/{dataset.id}/review"
    )
    feed_details_link = f"https://publish.{base_url}/{dataset_page_path}"

    payload = {
        "feed_id": revision.dataset_id,
        "feed_name": revision.name,
        "feed_short_description": revision.description,
        "dataset_type": dataset.dataset_type,
        "feed_detail_link": feed_details_link,
        "report_link": f"{feed_details_link}/pti-csv",
        "user_type": modified_by.account_type,
        "comments": revision.comment,
    }

    notification = get_notifications()
    if modified_by.account_type == AGENT_USER:
        organisation_repo = OrganisationOrganisationRepo(db)
        organisation = organisation_repo.get_by_id(dataset.organisation_id)
        payload["organisation"] = organisation.name
        notification.send_agent_data_endpoint_validation_error_notification(
            modified_by.email, revision.modified, False, **payload
        )
    else:
        notification.send_data_endpoint_validation_error_notification(
            modified_by.email, revision.modified, False, **payload
        )


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

    if event_data.step_name in EMAIL_STEPS:
        send_failure_email(db, task_result.revision_id)


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Timetables ETL Statemachine Exception Handler
    """
    log.info("Exception Event", data=event)
    # Include all event details in every log
    configure_logging(event, context)

    parsed_event = ExceptionHandlerInputData(**event)
    log.error(
        "Step Failed",
        error_message=parsed_event.cause.error_message,
        error_details=parsed_event.cause,
    )

    db = SqlDB()
    handle_error(db, parsed_event)

    return {
        "statusCode": 200,
    }
