"""
Updating the DB Revision Hash
"""

from common_layer.database import SqlDB
from common_layer.database.repos import OrganisationDatasetRevisionRepo
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
