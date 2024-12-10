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


def make_transmodel_services(
    services: list[TXCService],
    revision: OrganisationDatasetRevision,
    file_attributes: OrganisationTXCFileAttributes,
) -> list[TransmodelService]:
    """
    Convert TXCService objects to TransmodelService objects for database insertion.
    """
    transmodel_services: list[TransmodelService] = []

    for service in services:
        line_names = get_line_names(services)

        # TODO: Handle flexible service when implemented in parser
        service_type = "standard"

        transmodel_service = TransmodelService(
            service_code=service.ServiceCode,
            name=line_names[0],
            other_names=line_names[1:],
            start_date=service.StartDate,
            service_type=service_type,
            end_date=service.EndDate,
            revision_id=revision.id,
            txcfileattributes_id=file_attributes.id,
        )

        transmodel_services.append(transmodel_service)
    log.info("Generated Transmodel Services", count=len(transmodel_services))
    return transmodel_services
