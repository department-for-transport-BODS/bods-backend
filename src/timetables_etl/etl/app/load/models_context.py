"""
Context grouping dataclasses
"""

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from common_layer.database.client import SqlDB
from common_layer.database.models.model_naptan import NaptanStopPoint
from common_layer.database.models.model_transmodel import TransmodelServicePattern
from common_layer.xml.txc.models.txc_data import TXCData
from common_layer.xml.txc.models.txc_journey_pattern import TXCJourneyPatternSection

from ..helpers.lookups import ReferenceDataLookups
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
