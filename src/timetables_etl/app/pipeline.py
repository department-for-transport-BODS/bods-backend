"""
ETL Pipeline
"""

from timetables_etl.app.transform.services import make_transmodel_services

from .models import TaskData, TransformedData
from .txc.models.txc_data import TXCData


class MissingLines(Exception):
    """Raised when a service has no lines defined"""

    def __init__(self, service: str):
        self.message = f"Service {service} has no lines defined"
        super().__init__(self.message)


def transform_data(data: TXCData, task_data: TaskData):
    """
    Transform Parsed TXC XML Data into SQLAlchmeny Database Models to apply
    """

    transmodel_services = make_transmodel_services(
        data.Services, task_data.revision, task_data.file_attributes
    )

    return TransformedData(transmodel_service=transmodel_services)
