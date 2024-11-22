"""
ETL Pipeline
"""

from structlog.stdlib import get_logger

from .database import BodsDB
from .load.transmodel_service import load_transmodel_service
from .load.transmodel_service_service_patterns import link_service_to_service_patterns
from .load.transmodel_servicepatterns import load_transmodel_service_patterns
from .models import TaskData
from .transform.stop_points import (
    create_stop_point_location_mapping,
    get_naptan_stops_from_db,
)
from .txc.models.txc_data import TXCData

log = get_logger()


class MissingLines(Exception):
    """Raised when a service has no lines defined"""

    def __init__(self, service: str):
        self.message = f"Service {service} has no lines defined"
        super().__init__(self.message)


def transform_data(txc: TXCData, task_data: TaskData, db: BodsDB):
    """
    Transform Parsed TXC XML Data into SQLAlchmeny Database Models to apply
    """
    db_stops = get_naptan_stops_from_db(txc.StopPoints, db)
    stop_mapping = create_stop_point_location_mapping(txc.StopPoints, db_stops)

    for service in txc.Services:

        transmodel_services = load_transmodel_service(service, task_data, db)
        service_patterns = load_transmodel_service_patterns(
            service, txc, task_data, stop_mapping, db
        )
        link_service_to_service_patterns(transmodel_services, service_patterns, db)
