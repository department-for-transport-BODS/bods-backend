"""
Transmodel Vehicle Journeys
"""

from typing import TypeGuard

from common_layer.database.models import (
    TransmodelServicePatternStop,
    TransmodelVehicleJourney,
)
from common_layer.database.repos import (
    TransmodelFlexibleServiceOperationPeriodRepo,
    TransmodelVehicleJourneyRepo,
)
from common_layer.xml.txc.models import (
    TXCData,
    TXCFlexibleJourneyPattern,
    TXCFlexibleVehicleJourney,
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCVehicleJourney,
)
from structlog.stdlib import get_logger

from ...load.service_pattern_stop import (
    process_flexible_pattern_stops,
    process_pattern_stops,
)
from ...transform.service_pattern_mapping import ServicePatternMapping
from ...transform.vehicle_journeys import (
    generate_flexible_service_operation_period,
    generate_pattern_vehicle_journeys,
)
from ..models_context import (
    OperatingProfileProcessingContext,
    ProcessPatternStopsContext,
    ServicePatternVehicleJourneyContext,
    VehicleJourneyProcessingContext,
)
from .vehicle_journey_operating_profile import process_operating_profile

log = get_logger()


def is_flexible_vehicle_journey(
    journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
) -> TypeGuard[TXCFlexibleVehicleJourney]:
    """Type guard to check if a journey is a flexible vehicle journey"""
    return isinstance(journey, TXCFlexibleVehicleJourney)


def is_standard_vehicle_journey(
    journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
) -> TypeGuard[TXCVehicleJourney]:
    """Type guard to check if a journey is a standard vehicle journey"""
    return isinstance(journey, TXCVehicleJourney)


def process_vehicle_journey_operations(
    journey_results: list[
        tuple[TransmodelVehicleJourney, TXCVehicleJourney | TXCFlexibleVehicleJourney]
    ],
    context: VehicleJourneyProcessingContext,
) -> None:
    """
    Process and save operations data for vehicle journeys
    """
    txc_serviced_orgs_dict = {
        org.OrganisationCode: org for org in context.txc_serviced_orgs
    }
    operating_profile_context = OperatingProfileProcessingContext(
        bank_holidays=context.bank_holidays,
        tm_serviced_orgs=context.tm_serviced_orgs,
        txc_serviced_orgs_dict=txc_serviced_orgs_dict,
        txc_services=context.txc_services,
        db=context.db,
    )

    log.debug(
        "Journey Operations processing started", journey_results=len(journey_results)
    )
    for tm_vj, txc_vj in journey_results:
        match txc_vj:
            case TXCVehicleJourney():
                process_operating_profile(tm_vj, txc_vj, operating_profile_context)
            case TXCFlexibleVehicleJourney():
                flexible_operating_periods = generate_flexible_service_operation_period(
                    tm_vj, txc_vj
                )
                if flexible_operating_periods:
                    TransmodelFlexibleServiceOperationPeriodRepo(
                        context.db
                    ).bulk_insert(flexible_operating_periods)
            case _:
                raise ValueError(f"Unknown vehicle journey type: {type(txc_vj)}")


def process_vehicle_journeys(
    txc_vjs: list[TXCVehicleJourney | TXCFlexibleVehicleJourney],
    txc_jp: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    context: VehicleJourneyProcessingContext,
) -> list[TransmodelVehicleJourney]:
    """
    Generate and insert Transmodel Vehicle Journeys
    """
    log.debug(
        "Processing Vehicle Journeys for Journey Pattern",
        journey_pattern_id=txc_jp.id,
        pattern_type=(
            "flexible" if isinstance(txc_jp, TXCFlexibleJourneyPattern) else "standard"
        ),
    )
    journey_results = generate_pattern_vehicle_journeys(
        txc_vjs, txc_jp, context.service_pattern
    )

    if not journey_results:
        log.warning("No vehicle journeys generated")
        return []

    tm_journeys = [result[0] for result in journey_results]

    results = TransmodelVehicleJourneyRepo(context.db).bulk_insert(tm_journeys)

    process_vehicle_journey_operations(
        journey_results,
        context,
    )

    log.info(
        "Processed vehicle journeys for Service Pattern",
        pattern_id=results[0].service_pattern_id if results else None,
        count=len(results),
        vj_ids=[vj.id for vj in results],
    )

    return results


def make_vj_list() -> list[TXCVehicleJourney | TXCFlexibleVehicleJourney]:
    """
    Create list of VJ for a Service Pattern
    """
    vehicle_journeys: list[TXCVehicleJourney | TXCFlexibleVehicleJourney] = []
    return vehicle_journeys


def get_journey_pattern_lookup(
    txc: TXCData,
) -> dict[str, TXCJourneyPattern | TXCFlexibleJourneyPattern]:
    """
    Create a lookup dictionary mapping journey pattern IDs to their objects.
    """
    jp_lookup: dict[str, TXCJourneyPattern | TXCFlexibleJourneyPattern] = {}
    for service in txc.Services:
        if service.StandardService:
            for jp in service.StandardService.JourneyPattern:
                jp_lookup[jp.id] = jp
    return jp_lookup


def find_service_pattern_vehicle_journeys(
    txc: TXCData,
    service_pattern_id: str,
    service_pattern_mapping: ServicePatternMapping,
) -> list[TXCVehicleJourney | TXCFlexibleVehicleJourney]:
    """
    Find all vehicle journeys that map to a specific service pattern.

    """
    service_pattern_vjs: list[TXCVehicleJourney | TXCFlexibleVehicleJourney] = []

    for vj in txc.VehicleJourneys:
        if vj.VehicleJourneyCode is None:
            continue

        if (
            vj.VehicleJourneyCode
            in service_pattern_mapping.vehicle_journey_to_service_pattern
        ):
            mapped_sp_id: str = (
                service_pattern_mapping.vehicle_journey_to_service_pattern[
                    vj.VehicleJourneyCode
                ]
            )
            if mapped_sp_id == service_pattern_id:
                service_pattern_vjs.append(vj)

    return service_pattern_vjs


def group_vehicle_journeys_by_pattern(
    vehicle_journeys: list[TXCVehicleJourney | TXCFlexibleVehicleJourney],
) -> dict[str, list[TXCVehicleJourney | TXCFlexibleVehicleJourney]]:
    """
    Group vehicle journeys by their journey pattern reference.
    """
    vjs_by_journey_pattern: dict[
        str, list[TXCVehicleJourney | TXCFlexibleVehicleJourney]
    ] = {}

    for vj in vehicle_journeys:
        if vj.JourneyPatternRef:
            jp_id: str = vj.JourneyPatternRef
            if jp_id not in vjs_by_journey_pattern:
                vjs_by_journey_pattern[jp_id] = []
            vjs_by_journey_pattern[jp_id].append(vj)

    return vjs_by_journey_pattern


def process_journey_pattern_vehicle_journeys(
    vjs: list[TXCVehicleJourney | TXCFlexibleVehicleJourney],
    txc_jp: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    txc: TXCData,
    context: ServicePatternVehicleJourneyContext,
) -> tuple[list[TransmodelVehicleJourney], list[TransmodelServicePatternStop]]:
    """
    Process vehicle journeys for a specific journey pattern.
    """
    vj_context: VehicleJourneyProcessingContext = VehicleJourneyProcessingContext(
        service_pattern=context.service_pattern,
        bank_holidays=context.bank_holidays,
        tm_serviced_orgs=context.serviced_orgs,
        txc_serviced_orgs=txc.ServicedOrganisations,
        txc_services=txc.Services,
        db=context.db,
    )

    tm_vjs: list[TransmodelVehicleJourney] = process_vehicle_journeys(
        vjs, txc_jp, vj_context
    )

    pattern_stops: list[TransmodelServicePatternStop] = []

    for tm_vj in tm_vjs:
        if not vjs:
            continue

        txc_vj: TXCVehicleJourney | TXCFlexibleVehicleJourney = vjs[0]

        if isinstance(txc_jp, TXCFlexibleJourneyPattern):
            if not is_flexible_vehicle_journey(txc_vj):
                log.error(
                    "Expected flexible vehicle journey",
                    pattern_id=txc_jp.id,
                    journey_type=type(txc_vj),
                )
                continue

            stops = process_flexible_pattern_stops(
                context.service_pattern,
                tm_vj,
                txc_jp,
                context.stops,
                context.db,
            )
            pattern_stops.extend(stops)
        else:  # TXCJourneyPattern
            if not is_standard_vehicle_journey(txc_vj):
                log.error(
                    "Expected standard vehicle journey",
                    pattern_id=txc_jp.id,
                    journey_type=type(txc_vj),
                )
                continue

            jp_sections: list[TXCJourneyPatternSection] = [
                section
                for section in txc.JourneyPatternSections
                if section.id in txc_jp.JourneyPatternSectionRefs
            ]

            stops = process_pattern_stops(
                tm_service_pattern=context.service_pattern,
                tm_vehicle_journey=tm_vj,
                txc_vehicle_journey=txc_vj,
                context=ProcessPatternStopsContext(
                    jp_sections, context.stops, context.db
                ),
            )
            pattern_stops.extend(stops)

    return tm_vjs, pattern_stops


def process_service_pattern_vehicle_journeys(
    txc: TXCData,
    reference_journey_pattern: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    context: ServicePatternVehicleJourneyContext,
) -> tuple[list[TransmodelVehicleJourney], list[TransmodelServicePatternStop]]:
    """
    Generate and save to DB Transmodel Vehicle Journeys for a Service Pattern

    Instead of processing a single journey pattern, this processes all vehicle journeys
    that map to the same service pattern, using the reference journey pattern for
    initial processing context.
    """
    # Log initial information about the processing task
    log.info(
        "Generating Transmodel Vehicle Journeys for Service Pattern",
        service_pattern_id=context.service_pattern.service_pattern_id,
        journey_pattern_count=len(context.sp_data.journey_pattern_ids),
        reference_journey_pattern_id=reference_journey_pattern.id,
        tm_service_pattern_id=context.service_pattern.id,
    )

    # Get journey pattern lookup
    jp_lookup = get_journey_pattern_lookup(txc)

    # Find and group vehicle journeys by journey pattern
    vjs_by_journey_pattern = group_vehicle_journeys_by_pattern(
        find_service_pattern_vehicle_journeys(
            txc,
            context.service_pattern.service_pattern_id,
            context.service_pattern_mapping,
        )
    )

    results = [
        process_journey_pattern_vehicle_journeys(vjs, jp_lookup[jp_id], txc, context)
        for jp_id, vjs in vjs_by_journey_pattern.items()
        if jp_id in jp_lookup
    ]

    all_tm_vjs = [vj for vjs, _ in results for vj in vjs]
    all_pattern_stops = [stop for _, stops in results for stop in stops]

    # Log results
    log.info(
        "Generated Transmodel Vehicle Journeys for Service Pattern",
        tm_vjs=len(all_tm_vjs),
        journey_patterns_processed=len(results),
        total_vehicle_journeys=sum(
            len(vjs) for _, vjs in vjs_by_journey_pattern.items()
        ),
        service_pattern_id=context.service_pattern.service_pattern_id,
        tm_service_pattern_id=context.service_pattern.id,
    )

    return all_tm_vjs, all_pattern_stops
