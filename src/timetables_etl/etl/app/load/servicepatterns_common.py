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
from common_layer.xml.txc.models.txc_vehicle_journey import TXCVehicleJourney
from common_layer.xml.txc.models.txc_vehicle_journey_flexible import (
    TXCFlexibleVehicleJourney,
)
from structlog.stdlib import get_logger

from ..models import PatternCommonStats
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


def get_matching_journey_patterns(
    service: TXCService,
    jp_ids: list[str],
) -> list[TXCJourneyPattern | TXCFlexibleJourneyPattern]:
    """
    Get journey patterns from a service that match the provided journey pattern IDs.
    """
    all_journey_patterns: list[TXCJourneyPattern | TXCFlexibleJourneyPattern] = []

    if service.StandardService is not None:
        all_journey_patterns.extend(service.StandardService.JourneyPattern)

    if service.FlexibleService is not None:
        all_journey_patterns.extend(service.FlexibleService.FlexibleJourneyPattern)

    # Find matching patterns
    matching_patterns = [jp for jp in all_journey_patterns if jp.id in jp_ids]

    if not matching_patterns and all_journey_patterns:
        log.error(
            "No matching journey patterns found",
            journey_pattern_ids=jp_ids,
            available_ids=[jp.id for jp in all_journey_patterns],
        )

    return matching_patterns


class NoMatchingJourneyPatternsForServicePattern(Exception):
    """Exception raised when no matching journey patterns are found for a service pattern."""

    def __init__(self, service_code: str, service_pattern_id: str, jp_ids: list[str]):
        self.service_code = service_code
        self.service_pattern_id = service_pattern_id
        self.jp_ids = jp_ids
        message = (
            "No JourneyPatterns found on service pattern"
            f"{service_pattern_id} service {service_code}"
        )
        super().__init__(message)


def get_reference_journey_pattern(
    service: TXCService, sp_id: str, journey_pattern_ids: list[str]
) -> TXCJourneyPattern | TXCFlexibleJourneyPattern:
    """
    Get the first journey pattern that matches one of the provided journey pattern IDs.

    """
    matching_journey_patterns = get_matching_journey_patterns(
        service, journey_pattern_ids
    )

    if not matching_journey_patterns:
        log.error(
            "No reference journey pattern found for service pattern",
            service_code=service.ServiceCode,
            service_pattern_id=sp_id,
            journey_pattern_ids=journey_pattern_ids,
        )
        raise NoMatchingJourneyPatternsForServicePattern(
            service_code=service.ServiceCode,
            service_pattern_id=sp_id,
            jp_ids=journey_pattern_ids,
        )

    return matching_journey_patterns[0]


def filter_vehicle_journeys(
    vehicle_journeys: list[TXCVehicleJourney | TXCFlexibleVehicleJourney],
    vehicle_journey_codes: list[str],
) -> list[TXCVehicleJourney | TXCFlexibleVehicleJourney]:
    """
    Filters a list of VehicleJourney objects to only include those with VehicleJourneyCode

    """
    vehicle_journey_id_set = set(vehicle_journey_codes)

    filtered_journeys: list[TXCVehicleJourney | TXCFlexibleVehicleJourney] = [
        journey
        for journey in vehicle_journeys
        if journey.VehicleJourneyCode in vehicle_journey_id_set
    ]

    return filtered_journeys


def process_pattern_common(
    service: TXCService,
    context: ProcessPatternCommonContext,
) -> PatternCommonStats:
    """
    Process common elements for both standard and flexible service patterns
    """
    log.info(
        "Processing Localities, Admin Areas and Bank Holidays",
        service_code=service.ServiceCode,
    )

    sp_data = context.service_pattern_mapping.service_pattern_metadata[
        context.service_pattern.service_pattern_id
    ]
    localities = process_pattern_localities(
        context.service_pattern, sp_data.stop_sequence, context.db
    )
    admin_areas = process_pattern_admin_areas(
        context.service_pattern, sp_data.stop_sequence, context.db
    )

    reference_journey_pattern = get_reference_journey_pattern(
        service, context.service_pattern.service_pattern_id, sp_data.journey_pattern_ids
    )
    bank_holidays = TransmodelBankHolidaysRepo(context.db).get_bank_holidays_lookup(
        service.StartDate, service.EndDate
    )

    # Get the vehicle journeys for this ServicePattern
    filtered_vehicle_journeys = filter_vehicle_journeys(
        context.txc.VehicleJourneys,
        sp_data.vehicle_journey_ids,
    )

    vj_context = ServicePatternVehicleJourneyContext(
        service_pattern=context.service_pattern,
        stops=sp_data.stop_sequence,
        naptan_stops_lookup=context.lookups.stops,
        bank_holidays=bank_holidays,
        serviced_orgs=context.lookups.serviced_orgs,
        service_pattern_mapping=context.service_pattern_mapping,
        sp_data=sp_data,
        db=context.db,
        vehicle_journeys=filtered_vehicle_journeys,
    )

    tm_vjs, tm_pattern_stops = process_service_pattern_vehicle_journeys(
        context.txc,
        reference_journey_pattern,
        vj_context,
    )

    tracks = load_vehicle_journey_tracks(
        reference_journey_pattern,
        tm_vjs,
        context.lookups.tracks,
        sp_data.stop_sequence,
        context.db,
    )

    return PatternCommonStats(
        localities=len(localities),
        admin_areas=len(admin_areas),
        vehicle_journeys=len(tm_vjs),
        pattern_stops=len(tm_pattern_stops),
        tracks=len(tracks),
    )
