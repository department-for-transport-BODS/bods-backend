"""
ETL Pipeline
"""

from pandas import DataFrame

from .txc.models.txc_data import TXCData


class MissingLines(Exception):
    """Raised when a service has no lines defined"""

    def __init__(self, service: str):
        self.message = f"Service {service} has no lines defined"
        super().__init__(self.message)


def transform_data(data: TXCData):
    """
    Execute TXC ETL Pipeline
    """
