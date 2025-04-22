"""
Naptan Info Fetching
"""

from common_layer.database.client import SqlDB
from common_layer.database.models import NaptanStopPoint
from common_layer.database.repos import NaptanStopPointRepo
from structlog.stdlib import get_logger

from tools.db_viewer.utils import csv_extractor

log = get_logger()


@csv_extractor()
def extract_stoppoint(db: SqlDB, atco_codes: list[str]) -> list[NaptanStopPoint]:
    """
    Extract naptan stoppoint details from DB.
    """
    repo = NaptanStopPointRepo(db)
    stop_points, missing_stops = repo.get_by_atco_codes(atco_codes)
    if missing_stops:
        log.warning("Some Stops were not found in DB", missing_stops=missing_stops)
    return stop_points
