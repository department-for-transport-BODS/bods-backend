"""
DownloadDataset Operations
"""

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.database.repos import OrganisationDatasetRevisionRepo
from download_dataset.app.models import DownloaderResponse
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
    log.info("Dataset revision updated with new file.")


def get_remote_file_name(
    revision: OrganisationDatasetRevision,
    response: DownloaderResponse,
) -> str:
    """
    Create the name for the remote file using the current date and timestamp
    """
    now = datetime.now(UTC).strftime(DT_FORMAT)
    url_path = Path(revision.url_link)
    if url_path.suffix in (".zip", ".xml"):
        name = unquote(url_path.name)
    else:
        name = f"remote_dataset_{revision.dataset_id}_{now}.{response.filetype}"
    return name
