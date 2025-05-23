"""
Associations for a Service Pattern
"""

from typing import Sequence

from common_layer.database.models import (
    NaptanStopPoint,
    TransmodelServicePattern,
    TransmodelServicePatternAdminAreas,
    TransmodelServicePatternLocality,
)
from structlog.stdlib import get_logger

log = get_logger()


def generate_pattern_localities(
    pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
) -> list[TransmodelServicePatternLocality]:
    """Generate locality associations for a pattern"""
    locality_ids = {stop.locality_id for stop in stops if stop.locality_id is not None}

    localities = [
        TransmodelServicePatternLocality(
            servicepattern_id=pattern.id,
            locality_id=loc_id,
        )
        for loc_id in sorted(locality_ids)
    ]

    log.info(
        "Generated locality associations",
        pattern_id=pattern.service_pattern_id,
        locality_count=len(localities),
        locality_db_ids=locality_ids,
    )

    return localities


def generate_pattern_admin_areas(
    pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
) -> list[TransmodelServicePatternAdminAreas]:
    """Generate admin area associations for a pattern"""
    admin_area_ids = {
        stop.admin_area_id for stop in stops if stop.admin_area_id is not None
    }

    admin_areas = [
        TransmodelServicePatternAdminAreas(
            servicepattern_id=pattern.id,
            adminarea_id=area_id,
        )
        for area_id in sorted(admin_area_ids)
    ]

    log.info(
        "Generated admin area associations",
        pattern_id=pattern.service_pattern_id,
        admin_area_count=len(admin_areas),
        admin_area_db_ids=admin_area_ids,
    )

    return admin_areas
