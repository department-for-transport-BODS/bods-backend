"""
Lambda function to archive the gtfsrt data
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.archiver import ArchiveDetails, GtfsrtSettings, process_archive
from common_layer.database.client import SqlDB
from common_layer.enums import CAVLDataFormat
from common_layer.json_logging import configure_logging
from structlog.contextvars import bind_contextvars, clear_contextvars
from structlog.stdlib import get_logger

log = get_logger()


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handler for archiving gtfstr data
    """
    configure_logging(event, context)
    bind_contextvars(archive_type="GTFSRT")

    try:
        gtfsrt_settings = GtfsrtSettings()
        gtfsrt_zip = ArchiveDetails(
            url=gtfsrt_settings.url,
            data_format=CAVLDataFormat.GTFSRT.value,
            file_extension=".bin",
            s3_file_prefix="gtfsrt",
            local_file_prefix="gtfsrt",
            bucket_name=gtfsrt_settings.bucket_name,
        )
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
        f"'{archived_file_name}' in bucket '{gtfsrt_settings.bucket_name}'",
    }
