"""
Processing of Services
"""

from structlog.stdlib import get_logger

from ..database.models import (
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
    TransmodelService,
)
from ..txc.helpers.service import get_line_names
from ..txc.models.txc_service import TXCService

log = get_logger()


def make_transmodel_service(
    service: TXCService,
    revision: OrganisationDatasetRevision,
    file_attributes: OrganisationTXCFileAttributes,
) -> TransmodelService:
    """
    Convert a single TXCService object to a TransmodelService object.
    """
    service_type = "standard"
    if service.FlexibleService:
        service_type = "flexible"
    line_names = get_line_names(service)
    return TransmodelService(
        service_code=service.ServiceCode,
        name=line_names[0],
        other_names=line_names[1:],
        start_date=service.StartDate,
        service_type=service_type,
        end_date=service.EndDate,
        revision_id=revision.id,
        txcfileattributes_id=file_attributes.id,
    )


def make_transmodel_services(
    services: list[TXCService],
    revision: OrganisationDatasetRevision,
    file_attributes: OrganisationTXCFileAttributes,
) -> list[TransmodelService]:
    """
    Convert multiple TXCService objects to TransmodelService objects for database insertion.
    """
    log.debug("Creating Tranmodel Services", service_count=len(services))
    transmodel_services = [
        make_transmodel_service(service, revision, file_attributes)
        for service in services
    ]
    log.info("Generated Transmodel Services", count=len(transmodel_services))
    return transmodel_services
