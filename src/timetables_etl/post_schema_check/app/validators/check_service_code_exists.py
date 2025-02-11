"""
Check if service code exists in published dataset
"""

from dataclasses import dataclass

from common_layer.database.client import SqlDB
from common_layer.database.models.model_organisation import OrganisationDataset
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.xml.txc.models import TXCData
from structlog.stdlib import get_logger

from ..models import ValidationResult

log = get_logger()


@dataclass
class ServiceRevisions:
    """Contains the mapping of services to their revisions and active status"""

    service_to_revision_map: dict[str, list[int]]
    live_revision_ids: set[int]
    active_services: set[str]

    @classmethod
    def empty(cls) -> "ServiceRevisions":
        """
        Returns empty ServiceRevisions
        """
        return cls({}, set(), set())


@dataclass
class PublishedServiceData:
    """Contains information about published services"""

    dataset_id: int
    service_codes: set[str]

    def to_validation_result(self) -> ValidationResult:
        """
        Convert Published Service Data to a ValidationResult
        """
        service_codes_list = list(self.service_codes)
        return ValidationResult(
            is_valid=False,
            error_code=f"PUBLISHED_DATASET:{self.dataset_id},SERVICE_CODES:{service_codes_list}",
            message=f"Found an existing published dataset \
            (ID: {self.dataset_id}) with service codes: {service_codes_list}",
        )


def validate_service_codes(txc_data: TXCData) -> tuple[list[str], ValidationResult]:
    """
    Validates the presence of service codes in TXC data and returns them if valid.
    Returns a tuple of (service_codes, validation_result).
    """
    if not txc_data.Services:
        log.info("No service codes provided in TXCData. Skipping validation.")
        return [], ValidationResult(is_valid=True)

    return [service.ServiceCode for service in txc_data.Services], ValidationResult(
        is_valid=True
    )


def get_live_service_revisions(service_codes: list[str], db: SqlDB) -> ServiceRevisions:
    """
    Maps service codes to their active revisions and returns active services.
    """
    txc_file_attributes_repo = OrganisationTXCFileAttributesRepo(db)
    txc_attributes = txc_file_attributes_repo.get_by_service_code(service_codes)

    service_to_revision_map = {}
    for attr in txc_attributes:
        service_to_revision_map.setdefault(attr.service_code, []).append(
            attr.revision_id
        )

    if not service_to_revision_map:
        log.info("No matching TXC attributes found for service codes.")
        return ServiceRevisions.empty()

    datasetrevision_repo = OrganisationDatasetRevisionRepo(db)
    live_datasetrevisions = datasetrevision_repo.get_live_revisions(
        [rev_id for rev_ids in service_to_revision_map.values() for rev_id in rev_ids]
    )

    # Map active dataset revisions back to their service codes
    live_revision_ids = {rev.id for rev in live_datasetrevisions}
    active_services = {
        service
        for service, rev_ids in service_to_revision_map.items()
        if any(r in live_revision_ids for r in rev_ids)
    }

    return ServiceRevisions(service_to_revision_map, live_revision_ids, active_services)


def get_published_services(
    active_revision_ids: set[int], db: SqlDB
) -> list[PublishedServiceData]:
    """
    Retrieves information about published services based on active revision IDs.
    """
    dataset_repo = OrganisationDatasetRepo(db)
    published_datasets: list[OrganisationDataset] = dataset_repo.get_published_datasets(
        list(active_revision_ids)
    )

    published_revision_ids = {ds.live_revision_id for ds in published_datasets}
    revision_to_dataset = {ds.live_revision_id: ds.id for ds in published_datasets}

    txc_file_attributes_repo = OrganisationTXCFileAttributesRepo(db)

    # Fetch attributes one revision at a time and combine results
    all_published_txc_attributes = []
    for revision_id in published_revision_ids:
        attributes = txc_file_attributes_repo.get_by_revision_id(revision_id)
        all_published_txc_attributes.extend(attributes)

    # Group services by dataset ID
    published_dataset_to_services: dict[int, set[str]] = {}
    for attr in all_published_txc_attributes:
        dataset_id = revision_to_dataset.get(attr.revision_id)
        if dataset_id:
            published_dataset_to_services.setdefault(dataset_id, set()).add(
                attr.service_code
            )

    return [
        PublishedServiceData(dataset_id, service_codes)
        for dataset_id, service_codes in published_dataset_to_services.items()
    ]


def check_service_code_exists(txc_data: TXCData, db: SqlDB) -> list[ValidationResult]:
    """
    Checks if a service code already exists in a published dataset
    """
    service_codes, validation_result = validate_service_codes(txc_data)
    if not validation_result.is_valid or not service_codes:
        return [validation_result]

    service_revisions = get_live_service_revisions(service_codes, db)

    if not service_revisions.active_services:
        log.info(
            "No active dataset revisions found for these service codes.",
            service_codes=txc_data.Services,
        )
        return [ValidationResult(is_valid=True)]

    published_services = get_published_services(service_revisions.live_revision_ids, db)

    if not published_services:
        return [ValidationResult(is_valid=True)]

    validation_results = []
    for published_service in published_services:
        log.warning(
            "Found an existing published dataset with",
            dataset_id=published_service.dataset_id,
            service_codes=list(published_service.service_codes),
        )
        validation_results.append(published_service.to_validation_result())

    return (
        validation_results if validation_results else [ValidationResult(is_valid=True)]
    )
