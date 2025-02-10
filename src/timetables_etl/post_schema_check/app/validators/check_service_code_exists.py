from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.txc.models.txc_data import TXCData
from structlog.stdlib import get_logger

from ..models import ValidationResult

log = get_logger()


def check_service_code_exists(txc_data: TXCData, db: SqlDB) -> list[ValidationResult]:
    """
    Checks if a service code already exists in a live dataset
    """
    if not txc_data.Services:  # Exit early if no services provided
        log.info("No service codes provided in TXCData. Skipping validation.")
        return [ValidationResult(is_valid=True)]

    service_codes = [service.ServiceCode for service in txc_data.Services]

    txc_file_attributes_repo = OrganisationTXCFileAttributesRepo(db)
    txc_attributes = txc_file_attributes_repo.get_by_service_code(service_codes)

    service_to_revision_map = {}
    for attr in txc_attributes:
        service_to_revision_map.setdefault(attr.service_code, []).append(
            attr.revision_id
        )

    if not service_to_revision_map:
        log.info("No matching TXC attributes found for service codes.")
        return [ValidationResult(is_valid=True)]

    datasetrevision_repo = OrganisationDatasetRevisionRepo(db)
    active_datasetrevisions = datasetrevision_repo.get_active_datasets(
        [rev_id for rev_ids in service_to_revision_map.values() for rev_id in rev_ids]
    )

    # Map active dataset revisions back to their service codes
    active_revision_ids = {rev.id for rev in active_datasetrevisions}
    active_services = {
        service
        for service, rev_ids in service_to_revision_map.items()
        if any(r in active_revision_ids for r in rev_ids)
    }

    if not active_services:
        log.info(
            "No active dataset revisions found for these service codes.",
            service_codes=txc_data.Services,
        )
        return [ValidationResult(is_valid=True)]

    dataset_repo = OrganisationDatasetRepo(db)
    published_datasets = dataset_repo.get_published(list(active_revision_ids))

    # Determine which service codes have published datasets
    published_revision_ids = {ds.revision_id for ds in published_datasets}

    # Fetch all services for published revisions (not just the initially searched ones)
    all_published_txc_attributes = txc_file_attributes_repo.get_by_revision_id(
        list(published_revision_ids)
    )

    # Map published dataset revisions to all their service codes
    published_dataset_to_services = {}
    revision_to_dataset = {ds.revision_id: ds.id for ds in published_datasets}

    for attr in all_published_txc_attributes:
        dataset_id = revision_to_dataset.get(attr.revision_id)
        if dataset_id:
            published_dataset_to_services.setdefault(dataset_id, set()).add(
                attr.service_code
            )

    validation_results = []
    for dataset_id, service_codes in published_dataset_to_services.items():
        log.warning(
            "Found an existing published dataset with",
            dataset_id=dataset_id,
            service_codes=list(service_codes),
        )
        validation_results.append(
            ValidationResult(
                is_valid=False,
                error_code=f"PUBLISHED_DATASET:{dataset_id},SERVICE_CODES:{list(service_codes)}",
                message=f"Found an existing published dataset (ID: {dataset_id}) with service codes: {list(service_codes)}",
            )
        )

    return (
        validation_results if validation_results else [ValidationResult(is_valid=True)]
    )
