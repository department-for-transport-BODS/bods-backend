import time
from common_layer.archiver import GTFSRTArchiver
from common_layer.logger import logger
from os import environ


def lambda_handler(event, context):
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
        logger.info(_prefix + "Begin archiving GTFSRT data.")
        start = time.time()
        archiver = GTFSRTArchiver(url)
        archiver.archive()
        end = time.time()
        logger.info(_prefix + f"Finished archiving in {end-start:.2f} seconds.")
    except Exception as e:
        logger.error(f"GTFSRT zip task failed due to {e}")
    return
