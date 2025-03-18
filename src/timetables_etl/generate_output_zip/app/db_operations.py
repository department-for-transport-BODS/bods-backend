"""
Updating the DB Revision Hash
"""

from common_layer.aws.step import MapResults
from common_layer.database import SqlDB
from common_layer.database.models import ETLErrorCode, OrganisationDatasetRevision
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.db.constants import StepName
from common_layer.enums import FeedStatus
from structlog.stdlib import get_logger

from .models import ProcessingResult

log = get_logger()


def update_revision_hash(db: SqlDB, revision_id: int, file_hash: str):
    """
    Update the Revision Hash with the Hash of the File
    """
    OrganisationDatasetRevisionRepo(db).update_modified_file_hash(
        revision_id, file_hash
    )
    log.info("Updated Revision Hash", revision_id=revision_id, file_hash=file_hash)


def update_task_and_revision_status(
    db: SqlDB,
    map_results: MapResults,
    processing_result: ProcessingResult,
    dataset_etl_task_result_id: int,
    dataset_revision_id: int,
) -> OrganisationDatasetRevision:
    """
    Update the DatasetEtlTaskResult and Revision status to
    success or failure based on the given map_results and processing_result

    Returns:
        revision: The updated DatasetRevision record
    """

    task_result = ETLTaskResultRepo(db).require_by_id(dataset_etl_task_result_id)

    revision = OrganisationDatasetRevisionRepo(db).require_by_id(dataset_revision_id)

    # No succeeded => all files in Map Run failed
    no_valid_files: bool = len(map_results.succeeded) == 0
    # Files succeeded in map run but failed during re-zip
    failed_rezip_files: bool = (
        not (no_valid_files) and processing_result.failed_files != 0
    )

    has_error: bool = no_valid_files or failed_rezip_files

    if has_error:
        if no_valid_files:
            message = "No valid files to process"
            error_code = ETLErrorCode.NO_VALID_FILE_TO_PROCESS
        else:
            message = "Files failed during re-zipping process"
            error_code = ETLErrorCode.SYSTEM_ERROR

        revision.status = FeedStatus.ERROR
        ETLTaskResultRepo(db).mark_error(
            task_id=task_result.id,
            task_name=StepName.GENERATE_OUTPUT_ZIP.value,
            error_code=error_code,
            additional_info=message,
        )
    else:
        log.info("Setting task result and revision to success")
        ETLTaskResultRepo(db).mark_success(task_result.id)
        revision.status = FeedStatus.SUCCESS

    OrganisationDatasetRevisionRepo(db).update(revision)
    return revision


def publish_revision(db: SqlDB, revision: OrganisationDatasetRevision):
    """
    Publish the given revision
    """
    if revision.status == FeedStatus.SUCCESS:
        repo = OrganisationDatasetRevisionRepo(db)
        repo.publish_revision(revision.id)
    else:
        log.info(
            "Skipping publishing because revision status is not success",
            revision_status=revision.status,
        )


def update_live_revision(db: SqlDB, revision_id: int):
    """
    Link published revision to a dataset
    """
    revision = OrganisationDatasetRevisionRepo(db).require_by_id(revision_id)
    if revision.is_published is True and revision.status == FeedStatus.LIVE:
        repo = OrganisationDatasetRepo(db)
        repo.update_live_revision(revision.dataset_id, revision.id)
    else:
        log.info(
            "Skipping setting live_revision_id because revision \
            status is not live and is not published",
            revision_status=revision.status,
        )
