import time
from os import environ

from common_layer.archiver import GTFSRTArchiver
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

log = get_logger()


def lambda_handler(event, context):
    configure_logging()
    try:
        CAVL_CONSUMER_URL = environ.get("CAVL_CONSUMER_URL", default="")
        GTFS_API_BASE_URL = environ.get("GTFS_API_BASE_URL", default="")
        IS_NEW_GTFS_API_ACTIVE = environ.get("GTFS_API_ACTIVE", default=False) == "True"
        url = (
            f"{GTFS_API_BASE_URL}/gtfs-rt"
            if IS_NEW_GTFS_API_ACTIVE
            else f"{CAVL_CONSUMER_URL}/gtfsrtfeed"
        )
        _prefix = f"[GTFSRTArchiving] => "
        log.info(_prefix + "Begin archiving GTFSRT data.")
        start = time.time()
        archiver = GTFSRTArchiver(url)
        archiver.archive()
        end = time.time()
        log.info(_prefix + f"Finished archiving in {end-start:.2f} seconds.")
    except Exception:
        log.error("GTFSRT zip task failed", exc_info=True)
    return
