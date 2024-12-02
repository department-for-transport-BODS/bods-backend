"""
Transmodel Vehicle Journeys
"""

from datetime import date
from typing import Callable, Sequence, TypeGuard, TypeVar

from structlog.stdlib import get_logger

from timetables_etl.etl.app.transform.service_pattern_stops_flexible import (
    generate_flexible_pattern_stops,
)

from ..database.client import BodsDB
from ..database.models import (
    NaptanStopPoint,
    TransmodelServicedOrganisations,
    TransmodelServicedOrganisationWorkingDays,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelVehicleJourney,
)
from ..database.repos import (
    TransmodelFlexibleServiceOperationPeriodRepo,
    TransmodelNonOperatingDatesExceptionsRepo,
    TransmodelOperatingDatesExceptionsRepo,
    TransmodelOperatingProfileRepo,
    TransmodelServicedOrganisationVehicleJourneyRepo,
    TransmodelServicedOrganisationWorkingDaysRepo,
    TransmodelServicePatternStopRepo,
    TransmodelStopActivityRepo,
    TransmodelVehicleJourneyRepo,
)
from ..transform.service_pattern_stops import generate_pattern_stops
from ..transform.vehicle_journey_operations import (
    create_serviced_organisation_working_days,
    create_vehicle_journey_operations,
)
from ..transform.vehicle_journeys import (
    generate_flexible_service_operation_period,
    generate_pattern_vehicle_journeys,
)
from ..txc.models import (
    TXCData,
    TXCFlexibleJourneyPattern,
    TXCFlexibleVehicleJourney,
    TXCJourneyPattern,
    TXCJourneyPatternSection,
    TXCVehicleJourney,
)
from ..txc.models.txc_serviced_organisation import TXCServicedOrganisation

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


def process_pattern_stops(
    tm_service_pattern: TransmodelServicePattern,
    tm_vehicle_journey: TransmodelVehicleJourney,
    txc_vehicle_journey: TXCVehicleJourney | TXCFlexibleVehicleJourney,
    jp_sections: list[TXCJourneyPatternSection],
    stop_sequence: Sequence[NaptanStopPoint],
    db: BodsDB,
) -> list[TransmodelServicePatternStop]:
    """
    Process and insert transmodel_servicepatternstop
    """
    activity_map = TransmodelStopActivityRepo(db).get_activity_map()

    pattern_stops = generate_pattern_stops(
        tm_service_pattern,
        tm_vehicle_journey,
        txc_vehicle_journey,
        jp_sections,
        stop_sequence,
        activity_map,
    )

    results = TransmodelServicePatternStopRepo(db).bulk_insert(pattern_stops)

    log.info(
        "Saved Service Pattern Stops for Vehicle Journey",
        pattern_id=tm_service_pattern.id,
        vehicle_journey_id=tm_vehicle_journey.id,
        stop_count=len(results),
    )

    return results


def process_operating_profile(
    tm_vj: TransmodelVehicleJourney,
    txc_vj: TXCVehicleJourney,
    txc_serviced_orgs_dict: dict[str, TXCServicedOrganisation],
    bank_holidays: dict[str, list[date]],
    tm_serviced_orgs: dict[str, TransmodelServicedOrganisations],
    db: BodsDB,
):
    """
    Process a single Operating Profile
    """
    operations = create_vehicle_journey_operations(
        txc_vj=txc_vj,
        tm_vj=tm_vj,
        bank_holidays=bank_holidays,
        tm_serviced_orgs=tm_serviced_orgs,
        txc_serviced_orgs=txc_serviced_orgs_dict,
    )

    if operations.operating_profiles:
        TransmodelOperatingProfileRepo(db).bulk_insert(operations.operating_profiles)

    if operations.operating_dates:
        TransmodelOperatingDatesExceptionsRepo(db).bulk_insert(
            operations.operating_dates
        )

    if operations.non_operating_dates:
        TransmodelNonOperatingDatesExceptionsRepo(db).bulk_insert(
            operations.non_operating_dates
        )

    if operations.serviced_organisation_vehicle_journeys:
        saved_so_vjs = TransmodelServicedOrganisationVehicleJourneyRepo(db).bulk_insert(
            operations.serviced_organisation_vehicle_journeys
        )

        saved_map = {
            orig.id: saved
            for orig, saved in zip(
                operations.serviced_organisation_vehicle_journeys, saved_so_vjs
            )
        }

        working_days: list[TransmodelServicedOrganisationWorkingDays] = []
        for orig_vj, patterns in operations.working_days_patterns:
            saved_vj = saved_map[orig_vj.id]
            working_days.extend(
                create_serviced_organisation_working_days(saved_vj, patterns)
            )

        if working_days:
            TransmodelServicedOrganisationWorkingDaysRepo(db).bulk_insert(working_days)

    log.info(
        "Processed journey operations",
        journey_id=tm_vj.id,
        profiles=len(operations.operating_profiles),
        op_dates=len(operations.operating_dates),
        non_op_dates=len(operations.non_operating_dates),
        serviced_org_vjs=len(operations.serviced_organisation_vehicle_journeys),
    )


def process_vehicle_journey_operations(
    journey_results: list[
        tuple[TransmodelVehicleJourney, TXCVehicleJourney | TXCFlexibleVehicleJourney]
    ],
    bank_holidays: dict[str, list[date]],
    tm_serviced_orgs: dict[str, TransmodelServicedOrganisations],
    txc_serviced_orgs: list[TXCServicedOrganisation],
    db: BodsDB,
) -> None:
    """
    Process and save operations data for vehicle journeys
    """

    txc_serviced_orgs_dict = {org.OrganisationCode: org for org in txc_serviced_orgs}
    log.debug("Journey Results", journey_results=len(journey_results))
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
    tm_serviced_orgs: dict[str, TransmodelServicedOrganisations],
    txc_serviced_orgs: list[TXCServicedOrganisation],
    db: BodsDB,
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


T = TypeVar("T")


def process_vehicle_journeys_in_order(
    journeys: Sequence[TXCVehicleJourney | TXCFlexibleVehicleJourney],
    process_standard: Callable[[TXCVehicleJourney], T],
    process_flexible: Callable[[TXCFlexibleVehicleJourney], T],
) -> list[T]:
    """
    Process vehicle journeys in their original order, handling both types.
    """
    results: list[T] = []

    for journey in journeys:
        match journey:
            case TXCVehicleJourney():
                results.append(process_standard(journey))
            case TXCFlexibleVehicleJourney():
                results.append(process_flexible(journey))
            case _:
                raise ValueError(f"Unknown journey type: {type(journey)}")

    return results


def process_flexible_pattern_stops(
    tm_service_pattern: TransmodelServicePattern,
    tm_vehicle_journey: TransmodelVehicleJourney,
    flexible_pattern: TXCFlexibleJourneyPattern,
    stop_sequence: Sequence[NaptanStopPoint],
    db: BodsDB,
) -> list[TransmodelServicePatternStop]:
    """Process stops for flexible patterns"""
    activity_map = TransmodelStopActivityRepo(db).get_activity_map()

    pattern_stops = generate_flexible_pattern_stops(
        tm_service_pattern,
        tm_vehicle_journey,
        flexible_pattern,
        stop_sequence,
        activity_map,
    )

    results = TransmodelServicePatternStopRepo(db).bulk_insert(pattern_stops)

    log.info(
        "Saved Flexible Service Pattern Stops for Vehicle Journey",
        pattern_id=tm_service_pattern.id,
        vehicle_journey_id=tm_vehicle_journey.id,
        stop_count=len(results),
    )

    return results


def process_service_pattern_vehicle_journeys(
    txc: TXCData,
    txc_jp: TXCJourneyPattern | TXCFlexibleJourneyPattern,
    tm_service_pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
    bank_holidays: dict[str, list[date]],
    serviced_orgs: dict[str, TransmodelServicedOrganisations],
    db: BodsDB,
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
