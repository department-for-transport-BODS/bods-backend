
from common_layer.logger import logger


def lambda_handler(event, context):
    logger.info(f"Template Lambda Function: {event}")
    return
