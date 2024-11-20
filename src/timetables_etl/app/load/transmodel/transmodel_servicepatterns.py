"""
Transmodel Service Patterns Loader
"""

from shapely.geometry import Point
from structlog.stdlib import get_logger

from timetables_etl.app.txc.models.txc_service import TXCService

from ...database import BodsDB
from ...database.models import TransmodelServicePattern
from ...database.repos import TransmodelServicePatternRepo
from ...models import TaskData
from ...transform.service_patterns import make_service_patterns_from_service
from ...txc.models.txc_data import TXCData

log = get_logger()


def load_transmodel_service_patterns(
    service: TXCService,
    txc: TXCData,
    task_data: TaskData,
    stop_mapping: dict[str, Point],
    db: BodsDB,
) -> list[TransmodelServicePattern]:
    """
    Generate and load transmodel service patterns
    """
    data = make_service_patterns_from_service(
        service, task_data.revision, txc.JourneyPatternSections, stop_mapping
    )
    repo = TransmodelServicePatternRepo(db)
    result = repo.bulk_insert(data)
    log.info("Inserted Transmodel Service Patterns")
    return result
