"""
Context grouping dataclasses
"""

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from common_layer.database.client import SqlDB
from common_layer.database.models import NaptanStopPoint, TransmodelServicePattern
from common_layer.xml.txc.models import (
    TXCData,
    TXCJourneyPatternSection,
    TXCService,
    TXCServicedOrganisation,
)

from ..helpers.dataclasses import ReferenceDataLookups
from ..helpers.types import ServicedOrgLookup


@dataclass
class ProcessPatternCommonContext:
    """Context for pattern processing"""

    txc: TXCData
    service_pattern: TransmodelServicePattern
    stops: Sequence[NaptanStopPoint]
    lookups: ReferenceDataLookups
    db: SqlDB


@dataclass
class ServicePatternVehicleJourneyContext:
    """Context for vehicle journey processing"""

    service_pattern: TransmodelServicePattern
    stops: Sequence[NaptanStopPoint]
    bank_holidays: dict[str, list[date]]
    serviced_orgs: ServicedOrgLookup
    db: SqlDB


@dataclass
class ProcessPatternStopsContext:
    """Context for pattern stops processing"""

    jp_sections: list[TXCJourneyPatternSection]
    stop_sequence: Sequence[NaptanStopPoint]
    db: SqlDB


@dataclass
class VehicleJourneyProcessingContext:
    """Context for vehicle journey processing"""

    service_pattern: TransmodelServicePattern
    bank_holidays: dict[str, list[date]]
    tm_serviced_orgs: ServicedOrgLookup
    txc_serviced_orgs: list[TXCServicedOrganisation]
    txc_services: list[TXCService]
    db: SqlDB


@dataclass
class OperatingProfileProcessingContext:
    """
    Context Data required to create VJ Operating Profiles
    """

    bank_holidays: dict[str, list[date]]
    tm_serviced_orgs: ServicedOrgLookup
    txc_serviced_orgs_dict: dict[str, TXCServicedOrganisation]
    txc_services: list[TXCService]
    db: SqlDB
