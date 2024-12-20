"""
Transmodel Vehicle Journeys
"""

from datetime import date
from typing import Sequence, TypeGuard

from common_layer.database.client import SqlDB
from common_layer.database.models import NaptanStopPoint, TransmodelServicePattern
from common_layer.database.models.model_transmodel_vehicle_journey import (
    TransmodelVehicleJourney,
)
from common_layer.database.repos.repo_transmodel_flexible import (
    TransmodelFlexibleServiceOperationPeriodRepo,
)
from common_layer.database.repos.repo_transmodel_vehicle_journey import (
    TransmodelVehicleJourneyRepo,
)
from common_layer.txc.models import (
    TXCData,
    TXCFlexibleJourneyPattern,
    TXCFlexibleVehicleJourney,
    TXCJourneyPattern,
    TXCServicedOrganisation,
    TXCVehicleJourney,
)
from structlog.stdlib import get_logger

from ..helpers import ServicedOrgLookup
from ..load.service_pattern_stop import (
    process_flexible_pattern_stops,
    process_pattern_stops,
)
from ..transform.vehicle_journeys import (
    generate_flexible_service_operation_period,
    generate_pattern_vehicle_journeys,
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
    bank_holidays: dict[str, list[date]],
    tm_serviced_orgs: ServicedOrgLookup,
    txc_serviced_orgs: list[TXCServicedOrganisation],
    db: SqlDB,
) -> None:
    """
    Process and save operations data for vehicle journeys
    """

    txc_serviced_orgs_dict = {org.OrganisationCode: org for org in txc_serviced_orgs}
    log.debug(
        "Journey Operations processing started", journey_results=len(journey_results)
    )
    for tm_vj, txc_vj in journey_results:
        try:
            match txc_vj:
                case TXCVehicleJourney():
                    process_operating_profile(
                        tm_vj,
                        txc_vj,
                        txc_serviced_orgs_dict,
                        bank_holidays,
                        tm_serviced_orgs,
                        db,
                    )
                case TXCFlexibleVehicleJourney():
                    flexible_operating_periods = (
                        generate_flexible_service_operation_period(tm_vj, txc_vj)
                    )
                    if flexible_operating_periods:
                        TransmodelFlexibleServiceOperationPeriodRepo(db).bulk_insert(
                            flexible_operating_periods
                        )
                case _:
                    raise ValueError(f"Unknown vehicle journey type: {type(txc_vj)}")

        except Exception as e:
            log.error(
                "Failed to process journey operations",
                error=str(e),
                exc_info=True,
                journey_id=tm_vj.id,
            )
            continue


def process_vehicle_journeys(
    txc_vjs: list[TXCVehicleJourney | TXCFlexibleVehicleJourney],
    txc_jp: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    tm_service_pattern: TransmodelServicePattern,
    bank_holidays: dict[str, list[date]],
    tm_serviced_orgs: ServicedOrgLookup,
    txc_serviced_orgs: list[TXCServicedOrganisation],
    db: SqlDB,
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
        txc_vjs, txc_jp, tm_service_pattern
    )

    if not journey_results:
        log.warning("No vehicle journeys generated")
        return []

    tm_journeys = [result[0] for result in journey_results]

    results = TransmodelVehicleJourneyRepo(db).bulk_insert(tm_journeys)

    process_vehicle_journey_operations(
        journey_results, bank_holidays, tm_serviced_orgs, txc_serviced_orgs, db
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
    tm_service_pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
    bank_holidays: dict[str, list[date]],
    serviced_orgs: ServicedOrgLookup,
    db: SqlDB,
) -> list[TransmodelVehicleJourney]:
    """
    Generate and save to DB Transmodel Vehicle Journeys for a Service Pattern
    """
    # Get relevant vehicle journeys for this pattern
    log.info(
        "Generating Transmodel Vehicle Journeys for Service Pattern",
        txc_jp_id=txc_jp.id,
        pattern_type=(
            "flexible" if isinstance(txc_jp, TXCFlexibleJourneyPattern) else "standard"
        ),
        tm_service_pattern_id=tm_service_pattern.id,
    )
    vehicle_journeys = [
        vj for vj in txc.VehicleJourneys if vj.JourneyPatternRef == txc_jp.id
    ]

    tm_vjs = process_vehicle_journeys(
        vehicle_journeys,
        txc_jp,
        tm_service_pattern,
        bank_holidays,
        serviced_orgs,
        txc.ServicedOrganisations,
        db,
    )

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

                process_flexible_pattern_stops(
                    tm_service_pattern,
                    tm_vj,
                    txc_jp,
                    stops,
                    db,
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
                process_pattern_stops(
                    tm_service_pattern=tm_service_pattern,
                    tm_vehicle_journey=tm_vj,
                    txc_vehicle_journey=txc_vj,
                    jp_sections=jp_sections,
                    stop_sequence=stops,
                    db=db,
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
        tm_service_pattern_id=tm_service_pattern.id,
    )
    return tm_vjs
