"""
File Hashing Update Functions
"""

from pathlib import Path

from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.xml.txc.parser.hashing import get_file_hash
from structlog.stdlib import get_logger

from .models import ClamAVScannerInputData

log = get_logger()


def calculate_and_update_file_hash(
    db: SqlDB,
    input_data: ClamAVScannerInputData,
    file_path: Path,
):
    """
    Fetch the File from S3

    Update the database dataset revision with the File Hash
    """
    file_hash = get_file_hash(file_path)
    log.debug("Generated File Hash", hash=file_hash)

    OrganisationDatasetRevisionRepo(db).update_original_file_hash(
        input_data.revision_id, file_hash
    )
    log.info(
        "Generated File Hash and updated original_file_hash column in Dataset Revision",
        revision_id=input_data.revision_id,
        file_hash=file_hash,
        file_path=str(file_path),
    )
