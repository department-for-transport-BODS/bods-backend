import time
from common_layer.logger import logger
from os import environ
from common_layer.archiver import SiriVMArchiver


def lambda_handler(event, context):
    try:
        AVL_CONSUMER_API_BASE_URL = environ.get("AVL_CONSUMER_API_BASE_URL", default="")
        url = f"{AVL_CONSUMER_API_BASE_URL}/siri-vm"
        _prefix = f"[SIRIVM_Archiving] URL {url} => "
        logger.info(_prefix + "Begin archiving SIRIVM data.")
        start = time.time()
        archiver = SiriVMArchiver(url)
        archiver.archive()
        end = time.time()
        logger.info(_prefix + f"Finished archiving in {end-start:.2f} seconds.")
    except Exception as e:
        logger.error(f"SIRIVM zip task failed due to {str(e)}")
    return
