"""
Common Functions
"""

from typing import Sequence

from common_layer.database import SqlDB
from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicePattern,
    TransmodelServicePatternAdminAreas,
    TransmodelServicePatternLocality,
)
from common_layer.database.repos import (
    TransmodelBankHolidaysRepo,
    TransmodelServicePatternAdminAreaRepo,
    TransmodelServicePatternLocalityRepo,
)
from common_layer.xml.txc.models import (
    TXCFlexibleJourneyPattern,
    TXCJourneyPattern,
    TXCService,
)
from structlog.stdlib import get_logger

from ..transform.service_pattern_associations import (
    generate_pattern_admin_areas,
    generate_pattern_localities,
)
from .models_context import (
    ProcessPatternCommonContext,
    ServicePatternVehicleJourneyContext,
)
from .vehicle_journey import (
    load_vehicle_journey_tracks,
    process_service_pattern_vehicle_journeys,
)

log = get_logger()


def process_pattern_admin_areas(
    service_pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
    db: SqlDB,
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


def process_pattern_localities(
    service_pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
    db: SqlDB,
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


def process_pattern_common(
    service: TXCService,
    journey_pattern: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    context: ProcessPatternCommonContext,
) -> None:
    """
    Process common elements for both standard and flexible service patterns
    """
    log.info(
        "Processing Localities, Admin Areas and Bank Holidays",
        service_code=service.ServiceCode,
    )
    process_pattern_localities(context.service_pattern, context.stops, context.db)
    process_pattern_admin_areas(context.service_pattern, context.stops, context.db)

    bank_holidays = TransmodelBankHolidaysRepo(context.db).get_bank_holidays_lookup(
        service.StartDate, service.EndDate
    )

    vj_context = ServicePatternVehicleJourneyContext(
        service_pattern=context.service_pattern,
        stops=context.stops,
        bank_holidays=bank_holidays,
        serviced_orgs=context.lookups.serviced_orgs,
        db=context.db,
    )

    tm_vjs = process_service_pattern_vehicle_journeys(
        context.txc,
        journey_pattern,
        vj_context,
    )

    load_vehicle_journey_tracks(
        journey_pattern, tm_vjs, context.lookups.tracks, context.txc, context.db
    )
