import time
from boilerplate.archiver import SiriVMTFLArchiver
from boilerplate.logger import logger
from os import environ


def lambda_handler(event, context):
    try:
        AVL_CONSUMER_API_BASE_URL = environ.get("AVL_CONSUMER_API_BASE_URL", default="")
        url = f"{AVL_CONSUMER_API_BASE_URL}/siri-vm?downloadTfl=true"
        _prefix = f"[SIRIVM_TFL_Archiving] URL {url} => "
        logger.info(_prefix + "Begin archiving SIRIVM TFL data.")
        start = time.time()
        archiver = SiriVMTFLArchiver(event, url)
        archiver.archive()
        end = time.time()
        logger.info(_prefix + f"Finished archiving in {end-start:.2f} seconds.")
    except Exception as e:
        logger.error(f"SIRIVM TFL zip task failed due to {e}")
    return
