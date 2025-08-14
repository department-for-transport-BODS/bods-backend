"""
Description: Utility functions for boilerplate
"""

import hashlib
from os import environ
from typing import Union

import common_layer.aws.datadog.tracing  # type: ignore # pylint: disable=unused-import
from common_layer.database.client import SqlDB
from common_layer.database.repos import (
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationOrganisationRepo,
    UsersUserRepo,
)
from common_layer.notification import get_notifications
from structlog.stdlib import get_logger

AGENT_USER = 5
DATASET_TIMETABLE = 1
DATASET_FARES = 3


log = get_logger()


def sha1sum(content: Union[bytes, bytearray, memoryview]) -> str:
    """
    Takes the sha1 of a string and returns a hex string
    """
    return hashlib.sha1(content).hexdigest()


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

    if dataset is None:
        log.error("Unable to send email, dataset not found", revision_id=revision_id)
        return

    if revision.last_modified_user_id is None:
        log.error("Unable to send email, user not found", revision_id=revision_id)
        return

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
        "report_link": (
            ""
            if dataset.dataset_type == DATASET_FARES
            else f"{feed_details_link}/pti-csv"
        ),
        "user_type": modified_by.account_type,
        "comments": revision.comment,
        "organisation": "-",
    }

    notification = get_notifications()
    if modified_by.account_type == AGENT_USER:
        organisation_repo = OrganisationOrganisationRepo(db)
        organisation = organisation_repo.get_by_id(dataset.organisation_id)
        if organisation:
            payload["organisation"] = organisation.name
        notification.send_agent_data_endpoint_validation_error_notification(
            modified_by.email, revision.published_at, False, **payload
        )
    else:
        notification.send_data_endpoint_validation_error_notification(
            modified_by.email, revision.published_at, False, **payload
        )
