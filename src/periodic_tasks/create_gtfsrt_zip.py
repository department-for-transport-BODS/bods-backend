"""
Lambda function to archive the gtfsrt data
"""

import time
from os import environ
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.archiver import ArchiveDetails, archive_data
from common_layer.enums import CAVLDataFormat
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

log = get_logger()


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handler for archiving sirivm tfl data
    """
    event.update({"archive_type": "[GTFSRT_Archiving]"})
    configure_logging(event, context)
    bucket = environ.get("AWS_SIRIVM_STORAGE_BUCKET_NAME", None)
    file_name = None
    try:
        gtfs_api_active = environ.get("GTFS_API_ACTIVE", "False") == "True"
        url = (
            f"{environ.get('GTFS_API_BASE_URL', '')}/gtfs-rt"
            if gtfs_api_active
            else f"{environ.get('CAVL_CONSUMER_URL', '')}/gtfsrtfeed"
        )
        gtfsrt_zip = ArchiveDetails(
            url=url,
            data_format=CAVLDataFormat.GTFSRT.value,
            file_extension=".bin",
            s3_file_prefix="gtfsrt",
            local_file_prefix="gtfsrt",
        )

        log.info("Start archiving the data", details=gtfsrt_zip)
        start = time.time()
        archive_data(gtfsrt_zip)
        end = time.time()
        log.info("Finished archiving the data", time=end - start)

    except Exception as err:
        log.error("Archiving data failed", exc_info=True)
        raise err

    return {
        "statusCode": 200,
        "body": f"Successfully archived gtfsrt data to file '{file_name}' in bucket '{bucket}'",
    }
