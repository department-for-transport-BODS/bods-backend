"""
Flexible Stop Handling Functions
"""

from typing import Sequence

from common_layer.database.models import NaptanStopPoint
from common_layer.xml.txc.helpers.service import extract_flexible_pattern_stop_refs
from common_layer.xml.txc.models import TXCFlexibleJourneyPattern
from structlog.stdlib import get_logger

from ..helpers import StopsLookup

log = get_logger()


def map_stop_refs_to_naptan(
    stop_refs: list[str],
    atco_location_mapping: StopsLookup,
    journey_pattern_id: str,
) -> Sequence[NaptanStopPoint]:
    """
    Map stop references to NaptanStopPoint objects, logging any missing mappings.
    """
    stops: list[NaptanStopPoint] = []

    for stop_ref in stop_refs:
        if stop_ref in atco_location_mapping:
            stops.append(atco_location_mapping[stop_ref])
        else:
            log.warning(
                "stop_ref_not_found_in_mapping",
                stop_ref=stop_ref,
                journey_pattern_id=journey_pattern_id,
            )

    return stops


def get_flexible_pattern_stops(
    flexible_jp: TXCFlexibleJourneyPattern,
    atco_location_mapping: StopsLookup,
) -> Sequence[NaptanStopPoint]:
    """
    Get all NaptanStopPoint DB Models for a flexible journey pattern's stop sequence.
    """
    stop_refs = extract_flexible_pattern_stop_refs(flexible_jp)
    return map_stop_refs_to_naptan(stop_refs, atco_location_mapping, flexible_jp.id)
