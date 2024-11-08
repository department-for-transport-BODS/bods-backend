import time
from boilerplate.archiver import GTFSRTArchiver
from boilerplate.logger import logger
from os import environ


def lambda_handler(event, context):
    try:
        GTFS_API_BASE_URL = environ.get("GTFS_API_BASE_URL", default="")
        url = f"{GTFS_API_BASE_URL}/gtfs-rt"
        _prefix = f"[GTFSRTArchiving] URL {url} => "
        logger.info(_prefix + "Begin archiving GTFSRT data.")
        start = time.time()
        archiver = GTFSRTArchiver(event, url)
        archiver.archive()
        end = time.time()
        logger.info(_prefix + f"Finished archiving in {end-start:.2f} seconds.")
    except Exception as e:
        logger.error(f"GTFSRT zip task failed due to {e}")
    return
