"""
Transmodel Service Patterns Loader
"""

from common_layer.database import SqlDB
from common_layer.database.models import TransmodelServicePattern
from common_layer.xml.txc.models import TXCData, TXCService
from structlog.stdlib import get_logger

from ..helpers import ReferenceDataLookups
from ..models import PatternCommonStats, TaskData
from ..transform.service_pattern_mapping import (
    get_standard_service_pattern_ids,
    map_unique_journey_patterns,
)
from .models_context import ProcessPatternCommonContext, ProcessServicePatternContext
from .service_patterns_flexible import process_flexible_service_patterns
from .servicepatterns_common import process_pattern_common, process_service_pattern

log = get_logger()


def process_standard_service_patterns(
    service: TXCService,
    txc: TXCData,
    task_data: TaskData,
    lookups: ReferenceDataLookups,
    db: SqlDB,
) -> tuple[list[TransmodelServicePattern], PatternCommonStats]:
    """Process patterns for standard services"""
    patterns: list[TransmodelServicePattern] = []
    stats = PatternCommonStats()
    if not service.StandardService:
        return [], stats

    # pylint: disable=duplicate-code
    service_pattern_context = ProcessServicePatternContext(
        revision=task_data.revision,
        journey_pattern_sections=txc.JourneyPatternSections,
        stop_mapping=lookups.stops,
        flexible_zone_lookup=None,
        db=db,
    )

    service_pattern_mapping = map_unique_journey_patterns(txc, lookups)
    standard_service_pattern_ids = get_standard_service_pattern_ids(
        service.StandardService, service_pattern_mapping
    )

    for service_pattern_id in standard_service_pattern_ids:
        service_pattern = process_service_pattern(
            service,
            service_pattern_id,
            service_pattern_mapping,
            service_pattern_context,
        )
        common_context = ProcessPatternCommonContext(
            db=db,
            txc=txc,
            service_pattern=service_pattern,
            service_pattern_mapping=service_pattern_mapping,
            lookups=lookups,
            skip_track_inserts=task_data.input_data.skip_track_inserts,
        )

        stats += process_pattern_common(service, common_context)
        patterns.append(service_pattern)

    return patterns, stats


def load_transmodel_service_patterns(
    service: TXCService,
    txc: TXCData,
    task_data: TaskData,
    lookups: ReferenceDataLookups,
    db: SqlDB,
) -> tuple[list[TransmodelServicePattern], PatternCommonStats]:
    """
    Generate and load transmodel service patterns for both standard and flexible services
    """

    patterns: list[TransmodelServicePattern] = []
    stats = PatternCommonStats()
    if service.StandardService:
        log.info("Processing StandardService data", service_code=service.ServiceCode)
        service_patterns, stats = process_standard_service_patterns(
            service, txc, task_data, lookups, db
        )
        patterns.extend(service_patterns)

    if service.FlexibleService:
        log.info("Processing FlexibleService Data", service_code=service.ServiceCode)
        service_patterns, stats = process_flexible_service_patterns(
            service, txc, task_data, lookups, db
        )
        patterns.extend(service_patterns)

    if not patterns:
        log.warning(
            "No patterns processed",
            txc_service_code=service.ServiceCode,
            has_standard=service.StandardService is not None,
            has_flexible=service.FlexibleService is not None,
        )
        return patterns, stats

    log.info(
        "Loaded all Service Patterns",
        count=len(patterns),
        txc_service_code=service.ServiceCode,
    )
    return patterns, stats
