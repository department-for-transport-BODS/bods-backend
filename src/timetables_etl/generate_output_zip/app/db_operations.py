"""
Updating the DB Revision Hash
"""

from datetime import UTC, datetime

from common_layer.database import SqlDB
from common_layer.database.models.model_organisation import OrganisationDatasetRevision
from common_layer.database.models.model_pipelines import (
    DatasetETLTaskResult,
    ETLErrorCode,
    TaskState,
)
from common_layer.database.repos import OrganisationDatasetRevisionRepo
from common_layer.database.repos.repo_etl_task import ETLTaskResultRepo
from generate_output_zip.app.models.model_results import MapResults
from generate_output_zip.app.models.model_zip_processing import ProcessingResult
from structlog.stdlib import get_logger

log = get_logger()


def update_revision_hash(db: SqlDB, revision_id: int, file_hash: str):
    """
    Update the Revision Hash with the Hash of the File
    """
    OrganisationDatasetRevisionRepo(db).update_modified_file_hash(
        revision_id, file_hash
    )
    log.info("Updated Revision Hash", revision_id=revision_id, file_hash=file_hash)


def fetch_task_result(db: SqlDB, task_id: int) -> DatasetETLTaskResult:
    """
    Fetch task result from db
    """
    task_repo = ETLTaskResultRepo(db)
    task_result = task_repo.get_by_id(task_id)
    if task_result is None:
        raise ValueError("Dataset ETL Task Result Doesn't Exist")
    return task_result


def fetch_revision(db: SqlDB, revision_id: int) -> OrganisationDatasetRevision:
    """
    Fetch and validate revision existence
    """
    revision_repo = OrganisationDatasetRevisionRepo(db)
    revision = revision_repo.get_by_id(revision_id)
    if revision is None:
        raise ValueError("Cannot find OrganisationDatasetRevision")
    return revision


def update_task_success_state(
    task_result: DatasetETLTaskResult,
) -> DatasetETLTaskResult:
    """
    Update task state to success, resetting any error fields
    Returns updated task result without saving to DB
    """
    task_result.status = TaskState.SUCCESS
    task_result.completed = datetime.now(UTC)
    task_result.progress = 100

    # Reset any error fields just in case they were modified elsewhere
    task_result.task_name_failed = ""
    task_result.error_code = ETLErrorCode.EMPTY.value

    return task_result


def update_task_error_state(
    task_result: DatasetETLTaskResult, message: str, error_code: ETLErrorCode
) -> DatasetETLTaskResult:
    """
    Update the task state to error, with the code NO_VALID_FILES_TO_PROCESS
    """
    log.warning(message)
    task_result.status = TaskState.FAILURE
    task_result.error_code = error_code.value
    task_result.additional_info = message

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


def update_task_and_revision_status(
    db: SqlDB,
    map_results: MapResults,
    processing_result: ProcessingResult,
    dataset_etl_task_result_id: int,
    dataset_revision_id: int,
):
    """
    Update the DatasetEtlTaskResult and Revision status to
    success or failure based on the given map_results and processing_result
    """
    task_result = fetch_task_result(db, dataset_etl_task_result_id)
    revision = fetch_revision(db, dataset_revision_id)

    # No succeeded => all files in Map Run failed
    no_valid_files = len(map_results.succeeded) == 0

    # Files succeeded in map run but failed during re-zip
    no_sucessful_files = (
        not (no_valid_files) and processing_result.successful_files == 0
    )

    if no_valid_files:
        message = "No valid files to process"
        error_code = ETLErrorCode.NO_VALID_FILE_TO_PROCESS
        task_result = update_task_error_state(task_result, message, error_code)
    elif no_sucessful_files:
        message = "Files failed to upload"
        error_code = ETLErrorCode.SYSTEM_ERROR
        task_result = update_task_error_state(task_result, message, error_code)
        revision.status = TaskState.FAILURE.value
    else:
        log.info("Setting task result and revision to success")
        task_result = update_task_success_state(task_result)
        revision.status = TaskState.SUCCESS.value

    save_changes(db, task_result, revision)
