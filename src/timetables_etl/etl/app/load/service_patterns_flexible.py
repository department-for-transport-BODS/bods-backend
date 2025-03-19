"""
Flexible Service Pattern Handling
"""

from common_layer.database import SqlDB
from common_layer.database.models import TransmodelServicePattern
from common_layer.database.repos import TransmodelServicePatternRepo
from common_layer.xml.txc.models import TXCData, TXCService
from structlog.stdlib import get_logger

from ..helpers import ReferenceDataLookups
from ..models import PatternCommonStats, TaskData
from ..transform.service_pattern_mapping import map_unique_journey_patterns
from ..transform.service_patterns_flexible import create_flexible_service_pattern
from .models_context import (
    ProcessPatternCommonContext,
    ProcessServicePatternContext,
    ServicePatternMapping,
)
from .servicepatterns_common import process_pattern_common

log = get_logger()


def process_flexible_service_pattern(
    service: TXCService,
    service_pattern_id: str,
    service_pattern_mapping: ServicePatternMapping,
    context: ProcessServicePatternContext,
    db: SqlDB,
) -> TransmodelServicePattern:
    """
    Process a single Service Pattern
    """
    # pylint: disable=duplicate-code
    pattern = create_flexible_service_pattern(
        service, service_pattern_id, service_pattern_mapping, context
    )
    saved_pattern = TransmodelServicePatternRepo(db).insert(pattern)
    log.info(
        "Saved flexible service pattern",
        pattern_id=saved_pattern.service_pattern_id,
        db_id=saved_pattern.id,
    )
    return saved_pattern


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
        db=db,
    )

    service_pattern_mapping = map_unique_journey_patterns(txc, lookups)

    for service_pattern_id in service_pattern_mapping.service_pattern_metadata:
        service_pattern = process_flexible_service_pattern(
            service,
            service_pattern_id,
            service_pattern_mapping,
            service_pattern_context,
            db,
        )
        context = ProcessPatternCommonContext(
            txc=txc,
            service_pattern=service_pattern,
            service_pattern_mapping=service_pattern_mapping,
            lookups=lookups,
            db=db,
        )

        stats += process_pattern_common(service, context)
        patterns.append(service_pattern)

    log.info("Flexible Service Patterns Created", count=len(patterns))
    return patterns, stats
