"""
Description: Utility functions for boilerplate
"""

import hashlib
from datetime import datetime
from os import environ
from typing import Union

import common_layer.aws.datadog.tracing  # type: ignore # pylint: disable=unused-import
from common_layer.database.client import SqlDB
from common_layer.database.models import (
    OrganisationDataset,
    OrganisationDatasetRevision,
)
from common_layer.database.repos import (
    DataQualityPTIObservationRepo,
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationOrganisationRepo,
    UsersUserRepo,
)
from common_layer.database.repos.repo_data_quality import (
    DataQualityPTIValidationResultRepo,
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
    revision, dataset = get_dataset_details(db, revision_id)
    is_pti_compliant = get_dataset_pti_compliance(db, revision)

    if dataset is None:
        log.error("Unable to send email, dataset not found", revision_id=revision_id)
        return

    if revision.last_modified_user_id is None:
        log.error("Unable to send email, user not found", revision_id=revision_id)
        return

    user_repo = UsersUserRepo(db)
    modified_by = user_repo.require_by_id(revision.last_modified_user_id)

    feed_details_link = get_dataset_base_url(
        dataset.dataset_type, dataset.organisation_id, dataset.id
    )

    payload = {
        "feed_id": revision.dataset_id,
        "feed_name": revision.name,
        "feed_short_description": revision.description,
        "dataset_type": dataset.dataset_type,
        "feed_detail_link": feed_details_link,
        "report_link": (
            f"{feed_details_link}/fares-csv"
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
            modified_by.email, revision.published_at, is_pti_compliant, **payload
        )
    else:
        notification.send_data_endpoint_validation_error_notification(
            modified_by.email, revision.published_at, is_pti_compliant, **payload
        )


def get_dataset_base_url(
    dataset_type: int,
    organisation_id: int,
    dataset_id: int,
    revision_publish: bool = True,
) -> str:
    """Get the base path for timetable

    Args:
        dataset_type (int): fares or timetable
        organisation_id (int): organisation_id
        dataset_id (int): dataset id

    Returns:
        str: url for the details page
    """
    base_url = environ.get("FRONTEND_BASE_URL", "bus-data.dft.gov.uk")
    d_type = "timetable"
    if dataset_type == DATASET_FARES:
        d_type = "fares"

    dataset_page_path = f"org/{organisation_id}/dataset/{d_type}/{dataset_id}/"

    if revision_publish:
        dataset_page_path += "review"

    return f"https://publish.{base_url}/{dataset_page_path}"


def get_dataset_details(
    db: SqlDB, revision_id: int
) -> tuple[OrganisationDatasetRevision, OrganisationDataset | None]:
    """Method to get base dataset details

    Args:
        db (SqlDB): Database instance
        revision_id (int): revision id of dataset

    Returns:
        tuple[OrganisationDatasetRevision, OrganisationDataset | None]:
        Tuple containing the db objects
    """
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = revision_repo.require_by_id(revision_id)

    dataset_repo = OrganisationDatasetRepo(db)
    dataset = dataset_repo.get_by_id(int(revision.dataset_id))

    return (revision, dataset)


def get_dataset_pti_compliance(
    db: SqlDB, revision: OrganisationDatasetRevision
) -> bool:
    """Method will find it revision is published using PTI compliance or not

    Args:
        revision_id (int): revision id of the dataset

    Returns:
        bool: True if compliant/False is not compliant
    """
    pti_start_date = datetime.strptime(
        environ.get("PTI_START_DATE", "2021-04-01"), "%Y-%m-%d"
    )

    if revision.modified.date() < pti_start_date.date():  # type: ignore
        return False

    # compare if the date is less than today
    pti_validation_result_repo = DataQualityPTIValidationResultRepo(db)
    pti_validation_result = pti_validation_result_repo.get_by_revision_id(revision.id)

    pti_observation_result_repo = DataQualityPTIObservationRepo(db)
    pti_observation_results = pti_observation_result_repo.get_by_revision_id(
        revision.id
    )

    if pti_validation_result:
        return pti_validation_result.count == 0

    if pti_observation_results is None:
        pti_observation_results = []

    return len(pti_observation_results) == 0


def send_revision_published_notification(db: SqlDB, revision_id: int) -> None:
    """Method will trigger notifications to Operator/Agent and the sbscribers of the dataset
    On Successful publishing of the database

    Args:
        db (SqlDB): Database object for queries execution
        revision_id (int): Revision id of the dataset published
    """
    log.info(
        "Sending dataset published revision notification for revision:",
        revision_id=revision_id,
    )
    revision, dataset = get_dataset_details(db, revision_id)
    is_pti_compliant = get_dataset_pti_compliance(db, revision)

    if dataset is None:
        log.error("Unable to send email, dataset not found", revision_id=revision_id)
        return

    if revision.last_modified_user_id is None:
        log.error("Unable to send email, user not found", revision_id=revision_id)
        return

    notification = get_notifications()

    user_repo = UsersUserRepo(db)
    operator = user_repo.require_by_id(dataset.contact_id)

    organisation_repo = OrganisationOrganisationRepo(db)
    organisation = organisation_repo.get_by_id(dataset.organisation_id)

    operator_name = "-"
    if organisation:
        operator_name = organisation.name

    live_revision = False
    if dataset.live_revision_id:
        live_revision = True

    feed_details_link = get_dataset_base_url(
        dataset.dataset_type, dataset.organisation_id, dataset.id, live_revision
    )

    if operator.account_type != AGENT_USER and operator.is_active:
        notification.send_data_endpoint_publish_notification(
            contact_email=operator.email,
            dataset_id=dataset.id,
            dataset_name=revision.name,
            short_description=revision.short_description,
            published_at=revision.published_at,
            comments=revision.comment,
            feed_detail_link=feed_details_link,
            with_pti_violations=is_pti_compliant,
        )

    for agent in user_repo.fetch_agents_for_org(dataset.organisation_id):
        notification.send_agent_data_endpoint_publish_notification(
            agent.email,
            dataset_id=dataset.id,
            dataset_name=revision.name,
            short_description=revision.short_description,
            published_at=revision.published_at,
            comments=revision.comment,
            feed_detail_link=feed_details_link,
            operator_name=operator_name,
            with_pti_violations=is_pti_compliant,
        )

    for developer in user_repo.fetch_dataset_subscribers(dataset.id):
        notification.send_developer_data_endpoint_change_notification(
            developer.email,
            dataset_id=dataset.id,
            dataset_name=revision.name,
            operator_name=operator_name,
            last_updated=revision.published_at,
        )
