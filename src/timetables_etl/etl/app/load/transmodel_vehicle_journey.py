"""
Transmodel Vehicle Journeys
"""

from datetime import date
from typing import Sequence

from structlog.stdlib import get_logger

from ..database.client import BodsDB
from ..database.models import (
    NaptanStopPoint,
    TransmodelServicedOrganisations,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelVehicleJourney,
)
from ..database.repos import (
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
from ..transform.vehicle_journeys import generate_pattern_vehicle_journeys
from ..txc.models.txc_data import TXCData
from ..txc.models.txc_journey_pattern import TXCJourneyPatternSection
from ..txc.models.txc_service import TXCJourneyPattern
from ..txc.models.txc_serviced_organisation import TXCServicedOrganisation
from ..txc.models.txc_vehicle_journey import TXCVehicleJourney

log = get_logger()


def process_pattern_stops(
    tm_service_pattern: TransmodelServicePattern,
    tm_vehicle_journey: TransmodelVehicleJourney,
    txc_vehicle_journey: TXCVehicleJourney,
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


def process_vehicle_journey_operations(
    journey_results: list[tuple[TransmodelVehicleJourney, TXCVehicleJourney]],
    bank_holidays: dict[str, list[date]],
    tm_serviced_orgs: dict[str, TransmodelServicedOrganisations],
    txc_serviced_orgs: list[TXCServicedOrganisation],
    db: BodsDB,
) -> None:
    """
    Process and save operations data for vehicle journeys
    """

    txc_serviced_orgs_dict = {org.OrganisationCode: org for org in txc_serviced_orgs}

    for tm_vj, txc_vj in journey_results:
        try:
            operations = create_vehicle_journey_operations(
                txc_vj=txc_vj,
                tm_vj=tm_vj,
                bank_holidays=bank_holidays,
                tm_serviced_orgs=tm_serviced_orgs,
                txc_serviced_orgs=txc_serviced_orgs_dict,
            )

            if operations.operating_profiles:
                TransmodelOperatingProfileRepo(db).bulk_insert(
                    operations.operating_profiles
                )

            if operations.operating_dates:
                TransmodelOperatingDatesExceptionsRepo(db).bulk_insert(
                    operations.operating_dates
                )

            if operations.non_operating_dates:
                TransmodelNonOperatingDatesExceptionsRepo(db).bulk_insert(
                    operations.non_operating_dates
                )

            if operations.serviced_organisation_vehicle_journeys:
                saved_so_vjs = TransmodelServicedOrganisationVehicleJourneyRepo(
                    db
                ).bulk_insert(operations.serviced_organisation_vehicle_journeys)

                saved_map = {
                    orig.id: saved
                    for orig, saved in zip(
                        operations.serviced_organisation_vehicle_journeys, saved_so_vjs
                    )
                }

                working_days = []
                for orig_vj, patterns in operations.working_days_patterns:
                    saved_vj = saved_map[orig_vj.id]
                    working_days.extend(
                        create_serviced_organisation_working_days(saved_vj, patterns)
                    )

                if working_days:
                    TransmodelServicedOrganisationWorkingDaysRepo(db).bulk_insert(
                        working_days
                    )

            log.info(
                "Processed journey operations",
                journey_id=tm_vj.id,
                profiles=len(operations.operating_profiles),
                op_dates=len(operations.operating_dates),
                non_op_dates=len(operations.non_operating_dates),
                serviced_org_vjs=len(operations.serviced_organisation_vehicle_journeys),
            )

        except Exception as e:
            log.error(
                "Failed to process journey operations",
                error=str(e),
                exc_info=True,
                journey_id=tm_vj.id,
            )
            continue


def process_vehicle_journeys(
    txc_vjs: list[TXCVehicleJourney],
    txc_jp: TXCJourneyPattern,
    tm_service_pattern: TransmodelServicePattern,
    bank_holidays: dict[str, list[date]],
    tm_serviced_orgs: dict[str, TransmodelServicedOrganisations],
    txc_serviced_orgs: list[TXCServicedOrganisation],
    db: BodsDB,
) -> list[TransmodelVehicleJourney]:
    """
    Generate and insert Transmodel Vehicle Journeys
    """
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
        "Processed vehicle journeys",
        pattern_id=results[0].service_pattern_id if results else None,
        count=len(results),
        vj_ids=[vj.id for vj in results],
    )

    return results


def process_service_pattern_vehicle_journeys(
    txc: TXCData,
    txc_jp: TXCJourneyPattern,
    tm_service_pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
    bank_holidays: dict[str, list[date]],
    serviced_orgs: dict[str, TransmodelServicedOrganisations],
    db: BodsDB,
) -> list[TransmodelVehicleJourney]:
    """
    Generate and save to DB Transmodel Vehicle Journeys for a Service Pattern
    """
    tm_vjs = process_vehicle_journeys(
        txc.VehicleJourneys,
        txc_jp,
        tm_service_pattern,
        bank_holidays,
        serviced_orgs,
        txc.ServicedOrganisations,
        db,
    )

    jp_sections = [
        section
        for section in txc.JourneyPatternSections
        if section.id in txc_jp.JourneyPatternSectionRefs
    ]
    log.info(
        "Filtered Journey Pattern Sections by Journey Pattern",
        total_sections=len(txc.JourneyPatternSections),
        filtered_count=len(jp_sections),
        section_ids=[s.id for s in jp_sections],
    )
    for tm_vj in tm_vjs:
        process_pattern_stops(
            txc_vehicle_journey=next(
                j for j in txc.VehicleJourneys if j.JourneyPatternRef == txc_jp.id
            ),
            tm_vehicle_journey=tm_vj,
            tm_service_pattern=tm_service_pattern,
            jp_sections=jp_sections,
            stop_sequence=stops,
            db=db,
        )

    return tm_vjs
