import time
from os import environ

from common_layer.archiver import SiriVMArchiver
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

log = get_logger()


def lambda_handler(event, context):
    configure_logging()
    try:
        AVL_CONSUMER_API_BASE_URL = environ.get("AVL_CONSUMER_API_BASE_URL", default="")
        url = f"{AVL_CONSUMER_API_BASE_URL}/siri-vm"
        _prefix = f"[SIRIVM_Archiving] => "
        log.info(_prefix + "Begin archiving SIRIVM data.")
        start = time.time()
        archiver = SiriVMArchiver(url)
        archiver.archive()
        end = time.time()
        log.info(_prefix + f"Finished archiving in {end-start:.2f} seconds.")
    except Exception:
        log.error("SIRIVM zip task failed", exc_info=True)
    return
