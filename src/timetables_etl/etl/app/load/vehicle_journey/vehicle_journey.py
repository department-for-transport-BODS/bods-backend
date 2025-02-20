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
    TXCVehicleJourney,
)
from structlog.stdlib import get_logger

from ...load.service_pattern_stop import (
    process_flexible_pattern_stops,
    process_pattern_stops,
)
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


def process_service_pattern_vehicle_journeys(
    txc: TXCData,
    txc_jp: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    context: ServicePatternVehicleJourneyContext,
) -> tuple[list[TransmodelVehicleJourney], list[TransmodelServicePatternStop]]:
    """
    Generate and save to DB Transmodel Vehicle Journeys for a Service Pattern
    """
    log.info(
        "Generating Transmodel Vehicle Journeys for Service Pattern",
        txc_jp_id=txc_jp.id,
        pattern_type=(
            "flexible" if isinstance(txc_jp, TXCFlexibleJourneyPattern) else "standard"
        ),
        tm_service_pattern_id=context.service_pattern.id,
    )
    pattern_stops: list[TransmodelServicePatternStop] = []

    vehicle_journeys = [
        vj for vj in txc.VehicleJourneys if vj.JourneyPatternRef == txc_jp.id
    ]

    vj_context = VehicleJourneyProcessingContext(
        service_pattern=context.service_pattern,
        bank_holidays=context.bank_holidays,
        tm_serviced_orgs=context.serviced_orgs,
        txc_serviced_orgs=txc.ServicedOrganisations,
        txc_services=txc.Services,
        db=context.db,
    )

    tm_vjs = process_vehicle_journeys(vehicle_journeys, txc_jp, vj_context)

    for tm_vj in tm_vjs:
        txc_vj = next(j for j in vehicle_journeys if j.JourneyPatternRef == txc_jp.id)

        match txc_jp:
            case TXCFlexibleJourneyPattern():
                if not is_flexible_vehicle_journey(txc_vj):
                    log.error(
                        "Expected flexible vehicle journey",
                        pattern_id=txc_jp.id,
                        journey_type=type(txc_vj),
                    )
                    continue

                pattern_stops.extend(
                    process_flexible_pattern_stops(
                        context.service_pattern,
                        tm_vj,
                        txc_jp,
                        context.stops,
                        context.db,
                    )
                )
            case TXCJourneyPattern():
                if not is_standard_vehicle_journey(txc_vj):
                    log.error(
                        "Expected standard vehicle journey",
                        pattern_id=txc_jp.id,
                        journey_type=type(txc_vj),
                    )
                    continue

                jp_sections = [
                    section
                    for section in txc.JourneyPatternSections
                    if section.id in txc_jp.JourneyPatternSectionRefs
                ]

                pattern_stops.extend(
                    process_pattern_stops(
                        tm_service_pattern=context.service_pattern,
                        tm_vehicle_journey=tm_vj,
                        txc_vehicle_journey=txc_vj,
                        context=ProcessPatternStopsContext(
                            jp_sections, context.stops, context.db
                        ),
                    )
                )
            case _:
                raise ValueError(f"Unknown journey pattern type: {type(txc_jp)}")

    log.info(
        "Generated Transmodel Vehicle Journeys for Service Pattern",
        tm_vjs=len(tm_vjs),
        txc_jp_id=txc_jp.id,
        pattern_type=(
            "flexible" if isinstance(txc_jp, TXCFlexibleJourneyPattern) else "standard"
        ),
        tm_service_pattern_id=context.service_pattern.id,
    )
    return tm_vjs, pattern_stops
