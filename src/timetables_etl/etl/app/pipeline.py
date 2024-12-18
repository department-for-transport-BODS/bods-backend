"""
ETL Pipeline
"""

from common_layer.database import SqlDB
from common_layer.txc.models.txc_data import TXCData
from structlog.stdlib import get_logger

from .helpers import ReferenceDataLookups
from .load import (
    link_service_to_service_patterns,
    load_serviced_organizations,
    load_tracks,
    load_transmodel_service,
    load_transmodel_service_patterns,
    process_booking_arrangements,
)
from .models import TaskData
from .transform.stop_points import (
    create_stop_point_location_mapping,
    get_naptan_stops_from_db,
)

log = get_logger()


class MissingLines(Exception):
    """Raised when a service has no lines defined"""

    def __init__(self, service: str):
        self.message = f"Service {service} has no lines defined"
        super().__init__(self.message)


def build_lookup_data(txc: TXCData, db: SqlDB) -> ReferenceDataLookups:
    """
    Get from DB with inserts of reference data used accross the workflow
    """
    db_stops = get_naptan_stops_from_db(txc.StopPoints, db)
    stop_mapping = create_stop_point_location_mapping(txc.StopPoints, db_stops)

    serviced_orgs = load_serviced_organizations(txc.ServicedOrganisations, db)
    track_lookup = load_tracks(txc.RouteSections, db)

    return ReferenceDataLookups(
        stops=stop_mapping, serviced_orgs=serviced_orgs, tracks=track_lookup
    )


def transform_data(txc: TXCData, task_data: TaskData, db: SqlDB):
    """
    Transform Parsed TXC XML Data into SQLAlchmeny Database Models to apply
    """

    reference_data = build_lookup_data(txc, db)
    for service in txc.Services:

        tm_service = load_transmodel_service(service, task_data, db)
        process_booking_arrangements(service, tm_service, db)
        service_patterns = load_transmodel_service_patterns(
            service, txc, task_data, reference_data, db
        )
        link_service_to_service_patterns(tm_service, service_patterns, db)
