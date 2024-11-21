"""
Transmodel Vehicle Journeys
"""

from typing import Sequence

from structlog.stdlib import get_logger

from timetables_etl.app.database.client import BodsDB
from timetables_etl.app.database.models.model_naptan import NaptanStopPoint
from timetables_etl.app.database.models.model_transmodel import (
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelVehicleJourney,
)
from timetables_etl.app.database.repos.repo_transmodel import (
    TransmodelServicePatternStopRepo,
    TransmodelStopActivityRepo,
    TransmodelVehicleJourneyRepo,
)
from timetables_etl.app.transform.service_pattern_stops import generate_pattern_stops
from timetables_etl.app.transform.vehicle_journeys import (
    generate_pattern_vehicle_journeys,
)
from timetables_etl.app.txc.models.txc_data import TXCData
from timetables_etl.app.txc.models.txc_journey_pattern import TXCJourneyPatternSection
from timetables_etl.app.txc.models.txc_service import TXCJourneyPattern
from timetables_etl.app.txc.models.txc_vehicle_journey import TXCVehicleJourney

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


def process_service_pattern_vehicle_journeys(
    txc: TXCData,
    txc_jp: TXCJourneyPattern,
    tm_service_pattern: TransmodelServicePattern,
    stops: Sequence[NaptanStopPoint],
    db: BodsDB,
) -> list[TransmodelVehicleJourney]:
    """
    Generate and save to DB Transmodel Vehicle Journeys for a Service Pattern
    """
    tm_vjs = generate_pattern_vehicle_journeys(
        txc.VehicleJourneys, txc_jp, tm_service_pattern
    )
    results = TransmodelVehicleJourneyRepo(db).bulk_insert(tm_vjs)

    log.info(
        "Inserted Transmodel vehicle journeys",
        pattern_id=results[0].service_pattern_id if results else None,
        count=len(results),
        vj_ids=[vj.id for vj in results],
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
    return results
