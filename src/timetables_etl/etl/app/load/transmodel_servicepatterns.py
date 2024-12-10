"""
Transmodel Service Patterns Loader
"""

from typing import Sequence

from structlog.stdlib import get_logger

from ..database import BodsDB
from ..database.models import (
    NaptanStopPoint,
    OrganisationDatasetRevision,
    TransmodelServicedOrganisations,
    TransmodelServicePattern,
    TransmodelServicePatternAdminAreas,
    TransmodelServicePatternLocality,
)
from ..database.repos import (
    TransmodelBankHolidaysRepo,
    TransmodelServicePatternAdminAreaRepo,
    TransmodelServicePatternLocalityRepo,
    TransmodelServicePatternRepo,
)
from ..models import TaskData
from ..transform.service_pattern_associations import (
    generate_pattern_admin_areas,
    generate_pattern_localities,
)
from ..transform.service_patterns import create_service_pattern
from ..transform.utils_stops import get_pattern_stops
from ..txc.models import TXCJourneyPattern, TXCJourneyPatternSection, TXCService
from ..txc.models.txc_data import TXCData
from .transmodel_vehicle_journey import process_service_pattern_vehicle_journeys

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


def process_pattern_localities(
    service_pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
    db: BodsDB,
) -> list[TransmodelServicePatternLocality]:
    """
    Create and save locality associations for a pattern
    """
    localities = generate_pattern_localities(service_pattern, stops)
    results = TransmodelServicePatternLocalityRepo(db).bulk_insert(localities)

    log.info(
        "Saved locality associations",
        pattern_id=results[0].servicepattern_id if results else None,
        locality_count=len(results),
    )

    return results


def process_pattern_admin_areas(
    service_pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
    db: BodsDB,
) -> list[TransmodelServicePatternAdminAreas]:
    """
    Create and save admin area associations for a pattern

    """
    admin_areas = generate_pattern_admin_areas(service_pattern, stops)
    results = TransmodelServicePatternAdminAreaRepo(db).bulk_insert(admin_areas)

    log.info(
        "Saved admin area associations",
        pattern_id=results[0].servicepattern_id if results else None,
        admin_area_count=len(results),
    )

    return results


def load_transmodel_service_patterns(
    service: TXCService,
    txc: TXCData,
    task_data: TaskData,
    stop_mapping: dict[str, NaptanStopPoint],
    serviced_orgs: dict[str, TransmodelServicedOrganisations],
    db: BodsDB,
) -> list[TransmodelServicePattern]:
    """
    Generate and load transmodel service patterns
    """
    patterns: list[TransmodelServicePattern] = []

    if not service.StandardService:
        log.error("Non Standard Services not implemented")
        return patterns

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

        process_pattern_localities(service_pattern, stops, db)

        process_pattern_admin_areas(service_pattern, stops, db)

        bank_holidays = TransmodelBankHolidaysRepo(db).get_bank_holidays_lookup(
            service.StartDate, service.EndDate
        )
        process_service_pattern_vehicle_journeys(
            txc, txc_jp, service_pattern, stops, bank_holidays, serviced_orgs, db
        )

        patterns.append(service_pattern)

    log.info(
        "Loaded all Service Patterns patterns",
        count=len(patterns),
        txc_service_code=service.ServiceCode,
    )
    return patterns
