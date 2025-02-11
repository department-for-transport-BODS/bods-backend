"""
Lambda function to archive the sirivm tfl data
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
    event.update({"archive_type": "[SIRIVM_TFL_Archiving]"})
    configure_logging(event, context)
    bucket = environ.get("AWS_SIRIVM_STORAGE_BUCKET_NAME", None)
    file_name = None
    try:
        url = f"{environ.get('AVL_CONSUMER_API_BASE_URL', '')}/siri-vm?downloadTfl=true"
        sirivm_zip = ArchiveDetails(
            url=url,
            data_format=CAVLDataFormat.SIRIVM_TFL.value,
            file_extension=".xml",
            s3_file_prefix="sirivm_tfl",
            local_file_prefix="siri_tfl",
        )
        log.info("Start archiving the data", details=sirivm_zip)
        start = time.time()
        archive_data(sirivm_zip)
        end = time.time()
        log.info("Finished archiving the data", time=end - start)
    except Exception as err:
        log.error("Archiving data failed", exc_info=True)
        raise err
    return {
        "statusCode": 200,
        "body": f"Successfully archived sirivm tfl data to file '{file_name}' in bucket '{bucket}'",
    }
