"""
Lambda function to archive the sirivm data
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

BASE_URL = environ.get("AVL_CONSUMER_API_BASE_URL", "")


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handler for archiving sirivm data
    """
    configure_logging(event, context)
    bind_contextvars(archive_type="SRIVM")
    sirivm_zip = ArchiveDetails(
        url=f"{BASE_URL}/siri-vm",
        data_format=CAVLDataFormat.SIRIVM.value,
        file_extension=".xml",
        s3_file_prefix="sirivm",
        local_file_prefix="siri",
    )
    try:
        db = SqlDB()
        archived_name = process_archive(db, sirivm_zip)
    except Exception as e:
        log.error("Archiving sirivm data failed", exc_info=True)
        raise e
    finally:
        clear_contextvars()

    return {
        "statusCode": 200,
        "body": f"Successfully archived sirivm data to file "
        f"'{archived_name}' in bucket '{BUCKET_NAME}'",
    }
