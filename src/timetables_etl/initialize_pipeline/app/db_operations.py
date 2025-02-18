"""
DB Operations for InitializePipeline lambda
"""

from uuid import uuid4

from common_layer.database.client import SqlDB
from common_layer.database.models import (
    DatasetETLTaskResult,
    OrganisationDatasetRevision,
    TaskState,
)
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.database.repos.repo_data_quality import (
    DataQualityPostSchemaViolationRepo,
    DataQualityPTIObservationRepo,
    DataQualitySchemaViolationRepo,
)
from common_layer.database.repos.repo_organisation import (
    OrganisationTXCFileAttributesRepo,
)
from common_layer.enums import FeedStatus
from common_layer.exceptions.pipeline_exceptions import PipelineException
from structlog.stdlib import get_logger

log = get_logger()


def get_and_validate_revision(
    db: SqlDB, revision_id: int
) -> OrganisationDatasetRevision:
    """
    Retrieves and validates the existence of a dataset revision.
    """
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = revision_repo.get_by_id(revision_id)
    if revision is None:
        raise PipelineException(f"DatasetRevision with id {revision_id} not found.")
    return revision


def update_revision_status(db: SqlDB, revision: OrganisationDatasetRevision) -> None:
    """
    Updates the revision status to indexing.
    """
    log.debug(
        "Setting OrganisationDatasetRevision Status to indexing",
        dataset_revision_id=revision.id,
    )
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision.status = FeedStatus.INDEXING.value
    revision_repo.update(revision)


def create_task_result(db: SqlDB, revision_id: int) -> DatasetETLTaskResult:
    """
    Creates a new ETL task result entry.
    Returns:
        ID of the created task result
    """
    task_result_repo = ETLTaskResultRepo(db)
    task_result = DatasetETLTaskResult(
        revision_id=revision_id,
        status=TaskState.STARTED,
        task_id=str(uuid4()),
    )
    created_task_result = task_result_repo.insert(task_result)
    return created_task_result


def delete_existing_validation_violations(db: SqlDB, revision_id: int):
    """
    Delete any existing violations for the given revision id.
    This allows validation to occur multiple times for the same DatasetRevision

    Includes: SchemaViolation, PostSchemaViolation, and PTIObservation objects
    """
    schema_violation_repo = DataQualitySchemaViolationRepo(db)
    deleted_schema_violation_count = schema_violation_repo.delete_by_revision_id(
        revision_id
    )

    post_schema_violation_repo = DataQualityPostSchemaViolationRepo(db)
    deleted_post_schema_violation_count = (
        post_schema_violation_repo.delete_by_revision_id(revision_id)
    )

    pti_observation_repo = DataQualityPTIObservationRepo(db)
    deleted_pti_observation_count = pti_observation_repo.delete_by_revision_id(
        revision_id
    )

    total_deleted_count = (
        deleted_schema_violation_count
        + deleted_post_schema_violation_count
        + deleted_pti_observation_count
    )
    if total_deleted_count > 0:
        log.info(
            "Deleted existing validation violations for DatasetRevision",
            deleted_schema_violation_count=deleted_schema_violation_count,
            deleted_post_schema_violation_count=deleted_post_schema_violation_count,
            deleted_pti_observation_count=deleted_pti_observation_count,
            total_count=total_deleted_count,
        )
    else:
        log.info("No existing validation violations to delete")


def delete_existing_txc_file_attributes(db: SqlDB, revision_id: int):
    """
    Delete any existing TXCFileAttributes
    This allows validation to occur multiple times for the same DatasetRevision
    """
    file_attributes_repo = OrganisationTXCFileAttributesRepo(db)
    deleted_file_attributes_count = file_attributes_repo.delete_by_revision_id(
        revision_id
    )
    if deleted_file_attributes_count > 0:
        log.info(
            "Deleted existing TXCFileAttributes DatasetRevision",
            total_count=deleted_file_attributes_count,
        )
    else:
        log.info("No existing TXCFileAttributes to delete")
