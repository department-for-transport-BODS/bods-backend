"""
Transmodel Service Patterns Loader
"""

from dataclasses import dataclass

from common_layer.database import SqlDB
from common_layer.database.models import (
    OrganisationDatasetRevision,
    TransmodelServicePattern,
)
from common_layer.database.repos import TransmodelServicePatternRepo
from common_layer.xml.txc.models import (
    TXCData,
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCService,
)
from structlog.stdlib import get_logger

from ..helpers import ReferenceDataLookups, StopsLookup
from ..models import PatternCommonStats, TaskData
from ..transform.service_pattern_mapping import map_unique_journey_patterns
from ..transform.service_patterns import create_service_pattern
from ..transform.utils_stops import get_pattern_stops
from .models_context import ProcessPatternCommonContext
from .service_patterns_flexible import process_flexible_service_patterns
from .servicepatterns_common import process_pattern_common

log = get_logger()


@dataclass
class ProcessServicePatternContext:
    """Context for service pattern processing"""

    revision: OrganisationDatasetRevision
    journey_pattern_sections: list[TXCJourneyPatternSection]
    stop_mapping: StopsLookup
    db: SqlDB


def process_service_pattern(
    txc_service: TXCService,
    txc_jp: TXCJourneyPattern,
    context: ProcessServicePatternContext,
) -> TransmodelServicePattern:
    """
    Generate Service Pattern and Add to db
    Returns model instance with generated ID
    """
    pattern = create_service_pattern(
        txc_service,
        txc_jp,
        context.revision,
        context.journey_pattern_sections,
        context.stop_mapping,
    )
    saved_pattern = TransmodelServicePatternRepo(context.db).insert(pattern)

    log.info(
        "Saved service pattern",
        db_id=saved_pattern.id,
        pattern_id=saved_pattern.service_pattern_id,
    )

    return saved_pattern


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

    service_pattern_context = ProcessServicePatternContext(
        revision=task_data.revision,
        journey_pattern_sections=txc.JourneyPatternSections,
        stop_mapping=lookups.stops,
        db=db,
    )

    service_pattern_mapping = map_unique_journey_patterns(txc, lookups)
    log.critical(
        "Service Pattern Mapping Created",
        service_pattern_mapping=service_pattern_mapping,
    )

    for txc_jp in service.StandardService.JourneyPattern:
        service_pattern = process_service_pattern(
            service,
            txc_jp,
            service_pattern_context,
        )
        stops = get_pattern_stops(txc_jp, txc.JourneyPatternSections, lookups.stops)

        common_context = ProcessPatternCommonContext(
            db=db,
            txc=txc,
            service_pattern=service_pattern,
            stops=stops,
            lookups=lookups,
        )

        stats += process_pattern_common(service, txc_jp, common_context)
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
