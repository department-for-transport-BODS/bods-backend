"""
ETL Pipeline
"""

from timetables_etl.app.transform.service_patterns import (
    make_transmodels_service_patterns,
)
from timetables_etl.app.transform.services import make_transmodel_services
from timetables_etl.app.transform.stop_points import (
    create_stop_point_location_mapping,
    get_naptan_stops_from_db,
)

from .database import BodsDB
from .models import TaskData, TransformedData
from .txc.models.txc_data import TXCData


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
    transmodel_services = make_transmodel_services(
        txc.Services, task_data.revision, task_data.file_attributes
    )
    service_patterns = make_transmodels_service_patterns(
        txc, task_data.revision, stop_mapping
    )
    return TransformedData(
        transmodel_service=transmodel_services,
        transmodel_servicepatterns=service_patterns,
    )
