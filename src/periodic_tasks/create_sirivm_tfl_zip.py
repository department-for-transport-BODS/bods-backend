"""
Lambda function to archive the sirivm tfl data
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.archiver import ArchiveDetails, SirivmSettings, process_archive
from common_layer.database.client import SqlDB
from common_layer.enums import CAVLDataFormat
from common_layer.json_logging import configure_logging
from structlog.contextvars import bind_contextvars, clear_contextvars
from structlog.stdlib import get_logger

log = get_logger()


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handler for archiving sirivm tfl data
    """
    configure_logging(event, context)
    bind_contextvars(archive_type="SIRIVM_TFL")
    settings = SirivmSettings()
    sirivm_tfl_zip = ArchiveDetails(
        url=f"{settings.url}/siri-vm?downloadTfl=true",
        data_format=CAVLDataFormat.SIRIVM_TFL.value,
        file_extension=".xml",
        s3_file_prefix="sirivm_tfl",
        local_file_prefix="siri_tfl",
        bucket_name=settings.bucket_name,
    )

    try:

        db = SqlDB()
        archived_file_name = process_archive(db, sirivm_tfl_zip)
    except Exception as err_:
        log.error("Archiving sirivm tfl data failed", exc_info=True)
        raise err_
    finally:
        clear_contextvars()

    return {
        "statusCode": 200,
        "body": f"Successfully archived sirivm tfl data to file "
        f"'{archived_file_name}' in bucket '{settings.bucket_name}'",
    }
