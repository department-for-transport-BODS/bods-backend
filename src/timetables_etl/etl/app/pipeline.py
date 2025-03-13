"""
ETL Pipeline
"""

from common_layer.database import SqlDB
from common_layer.dynamodb.client.naptan_stop_points import (
    NaptanStopPointDynamoDBClient,
)
from common_layer.xml.txc.models import TXCData
from structlog.stdlib import get_logger

from .helpers import ReferenceDataLookups
from .load import (
    link_service_to_service_patterns,
    load_serviced_organizations,
    load_tracks,
    load_transmodel_service,
    process_booking_arrangements,
)
from .load.servicepatterns import load_transmodel_service_patterns
from .models import ETLProcessStats, TaskData
from .transform.stop_points import (
    create_stop_point_location_mapping,
    get_naptan_stops_from_dynamo,
)

log = get_logger()


class MissingLines(Exception):
    """Raised when a service has no lines defined"""

    def __init__(self, service: str):
        self.message = f"Service {service} has no lines defined"
        super().__init__(self.message)


def build_lookup_data(
    txc: TXCData, db: SqlDB, stop_point_client: NaptanStopPointDynamoDBClient
) -> ReferenceDataLookups:
    """
    Get from DB with inserts of reference data used accross the workflow
    """
    db_stops, missing_atco_codes = get_naptan_stops_from_dynamo(
        txc.StopPoints, stop_point_client
    )
    stop_mapping = create_stop_point_location_mapping(
        txc.StopPoints, db_stops, missing_atco_codes
    )

    serviced_orgs = load_serviced_organizations(txc.ServicedOrganisations, db)
    track_lookup = load_tracks(txc.RouteSections, db)

    return ReferenceDataLookups(
        stops=stop_mapping, serviced_orgs=serviced_orgs, tracks=track_lookup
    )


def transform_data(
    txc: TXCData,
    task_data: TaskData,
    db: SqlDB,
    stop_point_client: NaptanStopPointDynamoDBClient,
) -> ETLProcessStats:
    """
    Transform Parsed TXC XML Data into SQLAlchmeny Database Models to apply
    """
    stats = ETLProcessStats()
    reference_data = build_lookup_data(txc, db, stop_point_client)
    for service in txc.Services:

        tm_service = load_transmodel_service(service, task_data, db)
        stats.services += 1
        if not task_data.input_data.superseded_timetable:
            booking_arrangements = process_booking_arrangements(service, tm_service, db)
            service_patterns, pattern_stats = load_transmodel_service_patterns(
                service, txc, task_data, reference_data, db
            )
            link_service_to_service_patterns(tm_service, service_patterns, db)
            stats.booking_arrangements += len(booking_arrangements)
            stats.service_patterns += len(service_patterns)
            stats.pattern_stats += pattern_stats
        else:
            log.info(
                "Timetable is superceded. Only adding TransmodelService to DB",
                tm_service_id=tm_service.id,
                service_code=tm_service.service_code,
                service_name=tm_service.name,
            )
            stats.superseded_timetables += 1
    log.info("ETL Process Completed", stats=stats)
    return stats
