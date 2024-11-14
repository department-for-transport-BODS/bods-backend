"""
Processing of Services
"""

from timetables_etl.app.convertor.utils import get_line_names
from timetables_etl.app.database.models import (
    OrganisationDatasetrevision,
    TransmodelService,
)
from timetables_etl.app.pipeline import MissingLines
from timetables_etl.app.txc.models.txc_service import TXCService


def make_transmodel_services(
    services: list[TXCService],
    revision: OrganisationDatasetrevision,
    txc_file_id: int | None = None,
) -> list[TransmodelService]:
    """
    Convert TXCService objects to TransmodelService objects for database insertion.
    """
    transmodel_services: list[TransmodelService] = []

    for service in services:
        line_names = get_line_names(services)
        if len(line_names) < 1:
            raise MissingLines(service=service.ServiceCode)

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
            txcfileattributes_id=txc_file_id,
        )

        transmodel_services.append(transmodel_service)

    return transmodel_services
