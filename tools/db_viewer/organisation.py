"""
Organisation Data fetching
"""

from common_layer.database.models import (
    OrganisationDataset,
    OrganisationDatasetRevision,
    OrganisationOrganisation,
    OrganisationTXCFileAttributes,
)
from common_layer.database.repos import (
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationOrganisationRepo,
    OrganisationTXCFileAttributesRepo,
)
from structlog.stdlib import get_logger

from .utils import DatasetRevisionNotFoundError, SqlDB, csv_extractor

logger = get_logger()


@csv_extractor()
def extract_dataset_revision(
    db: SqlDB, revision_id: int
) -> OrganisationDatasetRevision:
    """
    Extract dataset revision from db.
    """
    repo = OrganisationDatasetRevisionRepo(db)
    result = repo.get_by_id(revision_id)

    if not result:
        logger.error("Dataset Revision Not Found", revision_id=revision_id)
        raise DatasetRevisionNotFoundError(revision_id)
    return result


@csv_extractor()
def extract_dataset(db: SqlDB, dataset_id: int) -> OrganisationDataset | None:
    """
    Extract the OrganisationDataset
    """
    repo = OrganisationDatasetRepo(db)
    return repo.get_by_id(dataset_id)


@csv_extractor()
def extract_organisation(
    db: SqlDB, organisation_id: int
) -> OrganisationOrganisation | None:
    """
    Extarct Organisation details from DB.
    """
    repo = OrganisationOrganisationRepo(db)
    return repo.get_by_id(organisation_id)


@csv_extractor()
def extract_txc_attributes(
    db: SqlDB, revision_id: int
) -> list[OrganisationTXCFileAttributes]:
    """
    Extract TXC file attributes from DB.
    """
    repo = OrganisationTXCFileAttributesRepo(db)
    return repo.get_by_revision_id(revision_id=revision_id)
