"""
Timetables Extraction
"""

from pathlib import Path

from common_layer.database.client import SqlDB
from common_layer.database.models import (
    TransmodelServicePattern,
    TransmodelServicePatternStop,
)
from structlog.stdlib import get_logger
from typer import BadParameter

from .naptan import extract_stoppoint
from .organisation import extract_org_info, extract_txc_attributes
from .transmodel import (
    extract_bookingarrangements,
    extract_flexibleserviceoperationperiod,
    extract_service_by_id,
    extract_service_service_patterns,
    extract_servicedorganisations,
    extract_servicedorganisationvehiclejourney,
    extract_servicedorganisationworkingdays,
    extract_servicepattern_localities,
    extract_servicepatterns_by_ids,
    extract_servicepatterns_by_revision_id,
    extract_servicepatternstop,
    extract_services_by_revision_id,
    extract_stopactivity,
    extract_tracks,
    extract_tracksvehiclejourney,
    extract_vehiclejourney,
)

log = get_logger()


def process_vehicle_journeys(
    db: SqlDB,
    service_pattern_stops: list[TransmodelServicePatternStop],
    output_path: Path,
):
    """
    Process Vehicle Journeys
    """
    vehicle_journey_ids = [
        result.vehicle_journey_id for result in service_pattern_stops
    ]
    extract_vehiclejourney(db, vehicle_journey_ids, output_path=output_path)
    extract_flexibleserviceoperationperiod(
        db, vehicle_journey_ids, output_path=output_path
    )
    serviced_org_vj = extract_servicedorganisationvehiclejourney(
        db, vehicle_journey_ids, output_path=output_path
    )
    extract_servicedorganisations(
        db,
        [it.serviced_organisation_id for it in serviced_org_vj],
        output_path=output_path,
    )
    extract_servicedorganisationworkingdays(
        db,
        [it.id for it in serviced_org_vj],
        output_path=output_path,
    )
    tracks_vj = extract_tracksvehiclejourney(
        db,
        vehicle_journey_ids,
        output_path=output_path,
    )
    track_ids = {track.tracks_id for track in tracks_vj}
    extract_tracks(db, track_ids, output_path=output_path)


def process_service_patterns(
    db: SqlDB,
    tm_service_patterns: list[TransmodelServicePattern],
    output_path: Path,
):
    """
    Items dependent on service patterns
    """
    service_pattern_ids = [result.id for result in tm_service_patterns]
    service_pattern_stops = extract_servicepatternstop(
        db, service_pattern_ids, output_path=output_path
    )
    extract_servicepattern_localities(db, service_pattern_ids, output_path=output_path)
    extract_stoppoint(
        db,
        [result.atco_code for result in service_pattern_stops],
        output_path=output_path,
    )
    stop_activity_ids = [result.stop_activity_id for result in service_pattern_stops]

    extract_stopactivity(db, stop_activity_ids, output_path=output_path)
    process_vehicle_journeys(db, service_pattern_stops, output_path)


def process_from_service_id(
    db: SqlDB,
    service_id: int,
    output_path: Path,
):
    """
    Process data from Service ID
    """
    log_ = log.bind(operation="batch_extraction")
    service = extract_service_by_id(db, service_id, output_path=output_path)
    if service is None:
        log_.error("Transmodel Service Not Found")
        raise BadParameter("Transmodel Service was not found in Database")
    extract_bookingarrangements(db, [service.id], output_path=output_path)
    service_service_patterns = extract_service_service_patterns(
        db, [service.id], output_path=output_path
    )
    service_pattern_ids = [sp.servicepattern_id for sp in service_service_patterns]
    service_patterns = extract_servicepatterns_by_ids(db, service_pattern_ids)
    process_service_patterns(db, service_patterns, output_path=output_path)


def process_from_revision_id(
    db: SqlDB,
    revision_id: int,
    output_path: Path,
):
    """
    Extract Data from DB and Output to CSVs based on table name
    """
    log_ = log.bind(operation="batch_extraction")
    log_.info("Starting DB Data extraction and output to CSV")

    # Organisation related entity
    extract_org_info(db, revision_id, output_path=output_path)
    extract_txc_attributes(db, revision_id, output_path=output_path)

    # Transmodel related entities
    tm_services = extract_services_by_revision_id(
        db, revision_id, output_path=output_path
    )
    service_ids = [it.id for it in tm_services]

    extract_service_service_patterns(db, service_ids, output_path=output_path)

    extract_bookingarrangements(db, service_ids, output_path=output_path)
    service_patterns = extract_servicepatterns_by_revision_id(
        db, revision_id, output_path=output_path
    )
    process_service_patterns(db, service_patterns, output_path)
