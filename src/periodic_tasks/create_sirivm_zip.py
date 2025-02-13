"""
Lambda function to archive the sirivm data
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
    Handler for archiving sirivm data
    """
    configure_logging(event, context)
    bind_contextvars(archive_type="SRIVM")

    try:
        srivim_settings = SirivmSettings()
        sirivm_zip = ArchiveDetails(
            url=f"{srivim_settings.url}/siri-vm",
            data_format=CAVLDataFormat.SIRIVM.value,
            file_extension=".xml",
            s3_file_prefix="sirivm",
            local_file_prefix="siri",
            bucket_name=srivim_settings.bucket_name,
        )
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
        f"'{archived_name}' in bucket '{srivim_settings.bucket_name}'",
    }
