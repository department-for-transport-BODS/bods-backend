"""
Common Functions
"""

from typing import Sequence

from structlog.stdlib import get_logger

from timetables_etl.etl.app.database import BodsDB
from timetables_etl.etl.app.database.models import (
    NaptanStopPoint,
    TransmodelServicePattern,
    TransmodelServicePatternAdminAreas,
    TransmodelServicePatternLocality,
)
from timetables_etl.etl.app.database.repos import (
    TransmodelServicePatternAdminAreaRepo,
    TransmodelServicePatternLocalityRepo,
)
from timetables_etl.etl.app.transform.service_pattern_associations import (
    generate_pattern_admin_areas,
    generate_pattern_localities,
)

from ..database import BodsDB
from ..database.models import (
    NaptanStopPoint,
    TransmodelServicedOrganisations,
    TransmodelServicePattern,
)
from ..database.repos import TransmodelBankHolidaysRepo
from ..load.transmodel_vehicle_journey import process_service_pattern_vehicle_journeys
from ..txc.models import (
    TXCData,
    TXCFlexibleJourneyPattern,
    TXCJourneyPattern,
    TXCService,
)

log = get_logger()


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


def process_pattern_common(
    service: TXCService,
    journey_pattern: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    service_pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
    txc: TXCData,
    serviced_orgs: dict[str, TransmodelServicedOrganisations],
    db: BodsDB,
) -> None:
    """
    Process common elements for both standard and flexible service patterns
    """
    log.info(
        "Processing Localities, Admin Areas and Bank Holidays",
        service_code=service.ServiceCode,
    )
    process_pattern_localities(service_pattern, stops, db)
    process_pattern_admin_areas(service_pattern, stops, db)

    bank_holidays = TransmodelBankHolidaysRepo(db).get_bank_holidays_lookup(
        service.StartDate, service.EndDate
    )
    process_service_pattern_vehicle_journeys(
        txc, journey_pattern, service_pattern, stops, bank_holidays, serviced_orgs, db
    )
