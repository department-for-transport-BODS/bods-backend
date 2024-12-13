import time
from common_layer.logger import logger
from common_layer.archiver import SiriVMArchiver
from os import environ


def lambda_handler(event, context):
    try:
        AVL_CONSUMER_API_BASE_URL = environ.get("AVL_CONSUMER_API_BASE_URL", default="")
        url = f"{AVL_CONSUMER_API_BASE_URL}/siri-vm"
        _prefix = f"[SIRIVM_Archiving] => "
        logger.info(_prefix + "Begin archiving SIRIVM data.")
        start = time.time()
        archiver = SiriVMArchiver(event, url)
        archiver.archive()
        end = time.time()
        logger.info(_prefix + f"Finished archiving in {end-start:.2f} seconds.")
    except Exception as e:
        logger.error(f"SIRIVM zip task failed due to {str(e)}")
    return
