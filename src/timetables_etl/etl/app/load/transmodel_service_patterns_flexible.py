"""
Flexible Service Pattern Handling
"""

from structlog.stdlib import get_logger

from ..database import BodsDB
from ..database.models import (
    NaptanStopPoint,
    OrganisationDatasetRevision,
    TransmodelServicedOrganisations,
    TransmodelServicePattern,
)
from ..database.repos import TransmodelServicePatternRepo
from ..models import TaskData
from ..transform.service_patterns_flexible import create_flexible_service_pattern
from ..transform.utils_stops_flexible import get_flexible_pattern_stops
from ..txc.models import TXCData, TXCFlexibleJourneyPattern, TXCService
from .transmodel_servicepatterns_common import process_pattern_common

log = get_logger()


def process_flexible_service_pattern(
    service: TXCService,
    jp: TXCFlexibleJourneyPattern,
    revision: OrganisationDatasetRevision,
    stop_mapping: dict[str, NaptanStopPoint],
    db: BodsDB,
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
    stop_mapping: dict[str, NaptanStopPoint],
    serviced_orgs: dict[str, TransmodelServicedOrganisations],
    db: BodsDB,
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
            stop_mapping,
            db,
        )
        stops = get_flexible_pattern_stops(flexible_jp, stop_mapping)

        process_pattern_common(
            service, flexible_jp, service_pattern, stops, txc, serviced_orgs, db
        )
        patterns.append(service_pattern)
    log.info("Flexible Service Patterns Created", count=len(patterns))
    return patterns
