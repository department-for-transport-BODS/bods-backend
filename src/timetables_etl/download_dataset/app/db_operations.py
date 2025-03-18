"""
DownloadDataset Operations
"""

from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.database.repos import OrganisationDatasetRevisionRepo
from structlog.stdlib import get_logger

log = get_logger()

DT_FORMAT = "%Y-%m-%d_%H-%M-%S"


def update_dataset_revision(
    db: SqlDB,
    revision: OrganisationDatasetRevision,
    file_name: str,
) -> None:
    """
    Update the dataset revision in the database with the new file name.
    Avoid querying the DB again by using the passed-in `revision` object.
    """
    repo = OrganisationDatasetRevisionRepo(db)
    if not revision.id:
        raise ValueError("Revision ID Missing")
    revision.upload_file = file_name
    repo.update(revision)
    log.info(
        "Dataset revision updated with new file.",
        revision_id=revision.id,
        revision_upload_file=revision.upload_file,
    )
