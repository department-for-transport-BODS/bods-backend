"""
Flexible Service Pattern Handling
"""

from common_layer.database import SqlDB
from common_layer.database.models import TransmodelServicePattern
from common_layer.xml.txc.models import TXCData, TXCService
from structlog.stdlib import get_logger

from ..helpers import ReferenceDataLookups
from ..models import PatternCommonStats, TaskData
from ..transform.service_pattern_mapping import (
    get_flexible_service_pattern_ids,
    map_unique_journey_patterns,
)
from .models_context import ProcessPatternCommonContext, ProcessServicePatternContext
from .servicepatterns_common import process_pattern_common, process_service_pattern

log = get_logger()


def process_flexible_service_patterns(
    service: TXCService,
    txc: TXCData,
    task_data: TaskData,
    lookups: ReferenceDataLookups,
    db: SqlDB,
) -> tuple[list[TransmodelServicePattern], PatternCommonStats]:
    """Process patterns for flexible services"""
    patterns: list[TransmodelServicePattern] = []
    stats = PatternCommonStats()
    if not service.FlexibleService:
        return [], stats

    service_pattern_context = ProcessServicePatternContext(
        revision=task_data.revision,
        journey_pattern_sections=txc.JourneyPatternSections,
        stop_mapping=lookups.stops,
        flexible_zone_lookup=lookups.flexible_zone_locations,
        db=db,
    )

    service_pattern_mapping = map_unique_journey_patterns(txc, lookups)
    flexible_service_pattern_ids = get_flexible_service_pattern_ids(
        service.FlexibleService, service_pattern_mapping
    )

    for service_pattern_id in flexible_service_pattern_ids:
        service_pattern = process_service_pattern(
            service,
            service_pattern_id,
            service_pattern_mapping,
            service_pattern_context,
        )
        context = ProcessPatternCommonContext(
            txc=txc,
            service_pattern=service_pattern,
            service_pattern_mapping=service_pattern_mapping,
            lookups=lookups,
            db=db,
            skip_track_inserts=task_data.input_data.skip_track_inserts,
        )

        stats += process_pattern_common(service, txc.RouteSections, context)
        patterns.append(service_pattern)

    log.info("Flexible Service Patterns Created", count=len(patterns))
    return patterns, stats
