"""
Dataclasses to reduce the number of input variables to functions
"""

from dataclasses import dataclass
from datetime import time
from typing import Sequence

from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelVehicleJourney,
)
from common_layer.xml.txc.models import (
    TXCFlexibleVehicleJourney,
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
    TXCVehicleJourney,
)

from ..helpers.types import LookupStopPoint, StopsLookup


@dataclass
class LinkContext:
    """
    Context variables for get_pattern_timing
    """

    current_link: TXCJourneyPatternTimingLink
    next_link: TXCJourneyPatternTimingLink | None
    is_first_stop: bool
    is_last_stop: bool


@dataclass
class StopData:
    """Data for a service pattern stop"""

    stop_usage: TXCJourneyPatternStopUsage
    naptan_stop: LookupStopPoint


@dataclass
class StopContext:
    """Context for creating a service pattern stop"""

    auto_sequence: int
    service_pattern: TransmodelServicePattern
    vehicle_journey: TransmodelVehicleJourney
    departure_time: time | None


@dataclass
class GeneratePatternStopsContext:
    """Context for generating pattern stops"""

    jp_sections: list[TXCJourneyPatternSection]
    stop_sequence: Sequence[NaptanStopPoint]
    stop_activity_id_map: dict[str, int]
    naptan_stops_lookup: StopsLookup


@dataclass
class JourneySectionContext:
    """Context for journey section processing"""

    service_pattern: TransmodelServicePattern
    vehicle_journey: TransmodelVehicleJourney
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney
    pattern_context: GeneratePatternStopsContext
    naptan_stops_lookup: StopsLookup


@dataclass
class SectionProcessingState:
    """State for processing journey pattern sections"""

    current_time: time | None
    auto_sequence: int
    pattern_stops: list[TransmodelServicePatternStop]
