"""
Lambda function to archive the gtfsrt data
"""

from os import environ
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from structlog.stdlib import get_logger
from structlog.contextvars import bind_contextvars, clear_contextvars
from common_layer.database.client import SqlDB
from common_layer.enums import CAVLDataFormat
from common_layer.json_logging import configure_logging
from common_layer.archiver import ArchiveDetails, process_archive, BUCKET_NAME


log = get_logger()

CAVL_URL = environ.get("CAVL_CONSUMER_URL", "")
BASE_URL = environ.get("GTFS_API_BASE_URL", "")
API_ACTIVE = environ.get("GTFS_API_ACTIVE", "False") == "True"


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handler for archiving gtfstr data
    """
    configure_logging(event, context)
    bind_contextvars(archive_type="GTFSRT")
    gtfsrt_zip = ArchiveDetails(
        url=f"{BASE_URL}/gtfs-rt" if API_ACTIVE else f"{CAVL_URL}/gtfsrtfeed",
        data_format=CAVLDataFormat.GTFSRT.value,
        file_extension=".bin",
        s3_file_prefix="gtfsrt",
        local_file_prefix="gtfsrt",
    )

    try:
        db = SqlDB()
        archived_file_name = process_archive(db, gtfsrt_zip)
    except Exception as _err:
        log.error("Archiving gtfstr data failed", exc_info=True)
        raise _err
    finally:
        clear_contextvars()

    return {
        "statusCode": 200,
        "body": f"Successfully archived gtfsrt data to file "
        f"'{archived_file_name}' in bucket '{BUCKET_NAME}'",
    }
