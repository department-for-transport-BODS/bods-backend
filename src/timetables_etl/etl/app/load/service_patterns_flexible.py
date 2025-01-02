"""
Flexible Service Pattern Handling
"""

from common_layer.database import SqlDB
from common_layer.database.models import (
    OrganisationDatasetRevision,
    TransmodelServicePattern,
)
from common_layer.database.repos import TransmodelServicePatternRepo
from common_layer.txc.models import TXCData, TXCFlexibleJourneyPattern, TXCService
from structlog.stdlib import get_logger

from ..helpers import ReferenceDataLookups, StopsLookup
from ..models import TaskData
from ..transform.service_patterns_flexible import create_flexible_service_pattern
from ..transform.utils_stops_flexible import get_flexible_pattern_stops
from .servicepatterns_common import process_pattern_common

log = get_logger()


def process_flexible_service_pattern(
    service: TXCService,
    jp: TXCFlexibleJourneyPattern,
    revision: OrganisationDatasetRevision,
    stop_mapping: StopsLookup,
    db: SqlDB,
) -> TransmodelServicePattern:
    """
    Process a single Service Pattern
    """
    pattern = create_flexible_service_pattern(service, jp, revision, stop_mapping)
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
) -> list[TransmodelServicePattern]:
    """Process patterns for flexible services"""
    patterns: list[TransmodelServicePattern] = []
    if not service.FlexibleService:
        return []
    for flexible_jp in service.FlexibleService.FlexibleJourneyPattern:
        service_pattern = process_flexible_service_pattern(
            service,
            flexible_jp,
            task_data.revision,
            lookups.stops,
            db,
        )
        stops = get_flexible_pattern_stops(flexible_jp, lookups.stops)

        process_pattern_common(
            service, flexible_jp, service_pattern, stops, txc, lookups, db
        )
        patterns.append(service_pattern)
    log.info("Flexible Service Patterns Created", count=len(patterns))
    return patterns
