"""
Transmodel Service Patterns Loader
"""

from structlog.stdlib import get_logger

from timetables_etl.app.database.models.model_junction import (
    TransmodelServicePatternAdminAreas,
    TransmodelServicePatternLocality,
)
from timetables_etl.app.database.models.model_naptan import NaptanStopPoint
from timetables_etl.app.database.repos.repo_junction import (
    TransmodelServicePatternAdminAreaRepo,
    TransmodelServicePatternLocalityRepo,
)
from timetables_etl.app.transform.service_pattern_associations import (
    generate_pattern_admin_areas,
    generate_pattern_localities,
)
from timetables_etl.app.transform.utils_stops import get_pattern_stops
from timetables_etl.app.txc.models.txc_service import TXCService

from ...database import BodsDB
from ...database.models import TransmodelServicePattern
from ...database.repos import TransmodelServicePatternRepo
from ...models import TaskData
from ...transform.service_patterns import create_service_pattern
from ...txc.models.txc_data import TXCData

log = get_logger()


def save_service_pattern(
    pattern: TransmodelServicePattern,
    db: BodsDB,
) -> TransmodelServicePattern:
    """Save pattern to database and return with ID"""
    pattern_repo = TransmodelServicePatternRepo(db)
    saved_pattern = pattern_repo.insert(pattern)

    log.info(
        "Saved service pattern",
        pattern_id=saved_pattern.service_pattern_id,
        db_id=saved_pattern.id,
    )

    return saved_pattern


def save_pattern_localities(
    localities: list[TransmodelServicePatternLocality],
    db: BodsDB,
) -> list[TransmodelServicePatternLocality]:
    """
    Create and save locality associations for a pattern
    """
    results = TransmodelServicePatternLocalityRepo(db).bulk_insert(localities)

    log.info(
        "Saved locality associations",
        pattern_id=results[0].servicepattern_id if results else None,
        locality_count=len(results),
    )

    return results


def save_pattern_admin_areas(
    admin_areas: list[TransmodelServicePatternAdminAreas],
    db: BodsDB,
) -> list[TransmodelServicePatternAdminAreas]:
    """
    Create and save admin area associations for a pattern

    """
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
    db: BodsDB,
) -> list[TransmodelServicePattern]:
    """
    Generate and load transmodel service patterns
    """
    patterns: list[TransmodelServicePattern] = []

    if not service.StandardService:
        log.error("Non Standard Services not implemented")
        return patterns

    for jp in service.StandardService.JourneyPattern:
        pattern = create_service_pattern(
            service, jp, task_data.revision, txc.JourneyPatternSections, stop_mapping
        )
        saved_pattern = save_service_pattern(pattern, db)

        stops = get_pattern_stops(jp, txc.JourneyPatternSections, stop_mapping)

        localities = generate_pattern_localities(saved_pattern, stops)
        save_pattern_localities(localities, db)

        admin_areas = generate_pattern_admin_areas(saved_pattern, stops)
        save_pattern_admin_areas(admin_areas, db)

        patterns.append(saved_pattern)

    log.info("Loaded all patterns", count=len(patterns))
    return patterns
