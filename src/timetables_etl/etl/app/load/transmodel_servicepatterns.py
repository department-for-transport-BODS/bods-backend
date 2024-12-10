"""
Transmodel Service Patterns Loader
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
from ..transform.service_patterns import create_service_pattern
from ..transform.utils_stops import get_pattern_stops
from ..txc.models import (
    TXCData,
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCService,
)
from .transmodel_service_patterns_flexible import process_flexible_service_patterns
from .transmodel_servicepatterns_common import process_pattern_common

log = get_logger()


def process_service_pattern(
    txc_service: TXCService,
    txc_jp: TXCJourneyPattern,
    revision: OrganisationDatasetRevision,
    journey_pattern_sections: list[TXCJourneyPatternSection],
    stop_mapping: dict[str, NaptanStopPoint],
    db: BodsDB,
) -> TransmodelServicePattern:
    """
    Generate Service Pattern and Add to db
    Returns model instance with generated ID
    """

    pattern = create_service_pattern(
        txc_service,
        txc_jp,
        revision,
        journey_pattern_sections,
        stop_mapping,
    )
    saved_pattern = TransmodelServicePatternRepo(db).insert(pattern)

    log.info(
        "Saved service pattern",
        pattern_id=saved_pattern.service_pattern_id,
        db_id=saved_pattern.id,
    )

    return saved_pattern


def process_standard_service_patterns(
    service: TXCService,
    txc: TXCData,
    task_data: TaskData,
    stop_mapping: dict[str, NaptanStopPoint],
    serviced_orgs: dict[str, TransmodelServicedOrganisations],
    db: BodsDB,
) -> list[TransmodelServicePattern]:
    """Process patterns for standard services"""
    patterns: list[TransmodelServicePattern] = []
    if not service.StandardService:
        return []
    for txc_jp in service.StandardService.JourneyPattern:
        service_pattern = process_service_pattern(
            service,
            txc_jp,
            task_data.revision,
            txc.JourneyPatternSections,
            stop_mapping,
            db,
        )
        stops = get_pattern_stops(txc_jp, txc.JourneyPatternSections, stop_mapping)

        process_pattern_common(
            service, txc_jp, service_pattern, stops, txc, serviced_orgs, db
        )
        patterns.append(service_pattern)

    return patterns


def load_transmodel_service_patterns(
    service: TXCService,
    txc: TXCData,
    task_data: TaskData,
    stop_mapping: dict[str, NaptanStopPoint],
    serviced_orgs: dict[str, TransmodelServicedOrganisations],
    db: BodsDB,
) -> list[TransmodelServicePattern]:
    """
    Generate and load transmodel service patterns for both standard and flexible services
    """
    patterns: list[TransmodelServicePattern] = []

    if service.StandardService:
        log.info("Processing StandardService data", service_code=service.ServiceCode)
        patterns.extend(
            process_standard_service_patterns(
                service, txc, task_data, stop_mapping, serviced_orgs, db
            )
        )

    if service.FlexibleService:
        log.info("Processing FlexibleService Data", service_code=service.ServiceCode)
        patterns.extend(
            process_flexible_service_patterns(
                service, txc, task_data, stop_mapping, serviced_orgs, db
            )
        )

    if not patterns:
        log.warning(
            "No patterns processed",
            txc_service_code=service.ServiceCode,
            has_standard=service.StandardService is not None,
            has_flexible=service.FlexibleService is not None,
        )
        return patterns

    log.info(
        "Loaded all Service Patterns",
        count=len(patterns),
        txc_service_code=service.ServiceCode,
    )
    return patterns
