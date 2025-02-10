"""
Models to pass context between functions
"""

from dataclasses import dataclass
from datetime import date

from common_layer.database.client import SqlDB
from common_layer.database.models import TransmodelServicePattern
from common_layer.xml.txc.models import TXCServicedOrganisation

from ...helpers.types import ServicedOrgLookup


@dataclass
class OperatingProfileProcessingContext:
    """
    Context Data required to create VJ Operating Profiles
    """

    bank_holidays: dict[str, list[date]]
    tm_serviced_orgs: ServicedOrgLookup
    txc_serviced_orgs_dict: dict[str, TXCServicedOrganisation]
    db: SqlDB


@dataclass
class VehicleJourneyProcessingContext:
    """Context for vehicle journey processing"""

    service_pattern: TransmodelServicePattern
    bank_holidays: dict[str, list[date]]
    tm_serviced_orgs: ServicedOrgLookup
    txc_serviced_orgs: list[TXCServicedOrganisation]
    db: SqlDB
