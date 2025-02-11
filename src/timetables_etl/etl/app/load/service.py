"""
Gen and load of Transmodel Services
"""

from common_layer.database import SqlDB
from common_layer.database.models import TransmodelService
from common_layer.database.repos import TransmodelServiceRepo
from common_layer.xml.txc.models.txc_service import TXCService
from structlog.stdlib import get_logger

from ..models import TaskData
from ..transform.services import make_transmodel_service

log = get_logger()


def load_transmodel_service(
    service: TXCService, task_data: TaskData, db: SqlDB
) -> TransmodelService:
    """
    Generate and Load Transmodel Service into DB
    """

    transmodel_service = make_transmodel_service(
        service, task_data.revision, task_data.file_attributes
    )
    repo = TransmodelServiceRepo(db)
    result = repo.insert(transmodel_service)
    log.info(
        "Inserted Transmodel Service into DB",
        service_id=result.id,
        name=result.name,
        service_code=result.service_code,
    )
    return result
