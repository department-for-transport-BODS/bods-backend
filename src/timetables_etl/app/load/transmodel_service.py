"""
Gen and load of Transmodel Services
"""

from structlog.stdlib import get_logger

from timetables_etl.app.txc.models.txc_service import TXCService

from ..database import BodsDB
from ..database.models import TransmodelService
from ..database.repos import TransmodelServiceRepo
from ..models import TaskData
from ..transform.services import make_transmodel_service

log = get_logger()


def load_transmodel_service(
    service: TXCService, task_data: TaskData, db: BodsDB
) -> TransmodelService:
    """
    Generate and Load Transmodel Services in to DB
    """

    transmodel_services = make_transmodel_service(
        service, task_data.revision, task_data.file_attributes
    )
    repo = TransmodelServiceRepo(db)
    result = repo.insert(transmodel_services)
    log.info("Inserted Transmodel Services into DB")
    return result
