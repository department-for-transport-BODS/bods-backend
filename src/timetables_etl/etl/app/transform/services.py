"""
Processing of Services
"""

from common_layer.database.models import (
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
    TransmodelService,
)
from common_layer.xml.txc.helpers.service import get_line_names
from common_layer.xml.txc.models.txc_service import TXCService
from structlog.stdlib import get_logger

log = get_logger()


def make_transmodel_service(
    service: TXCService,
    revision: OrganisationDatasetRevision,
    file_attributes: OrganisationTXCFileAttributes,
    superceded_timetable: bool,
) -> TransmodelService:
    """
    Convert a single TXCService object to a TransmodelService object.
    """
    service_type = "standard"
    if service.FlexibleService:
        service_type = "flexible"
    line_names = get_line_names(service)
    txcfileattributes_id = file_attributes.id if not superceded_timetable else None
    return TransmodelService(
        service_code=service.ServiceCode,
        name=line_names[0],
        other_names=line_names[1:],
        start_date=service.StartDate,
        service_type=service_type,
        end_date=service.EndDate,
        revision_id=revision.id,
        txcfileattributes_id=txcfileattributes_id,
    )
