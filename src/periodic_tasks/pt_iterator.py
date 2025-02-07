import logging
import os
from os import environ
from sys import stdout

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(environ.get("LOG_LEVEL", "DEBUG"))
handler = logging.StreamHandler(stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

client = boto3.client("lambda")


def lambda_handler(event, context):
    count = event["iterator"]["count"]
    index = event["iterator"]["index"] + 1

    target_functions = os.environ.get("TARGET_FUNCTION_NAMES")
    if not target_functions:
        raise ValueError("No target functions found in env TARGET_FUNCTION_NAMES")

    logger.info(f"Target functions to invoke: {target_functions}")

    function_names = target_functions.split(",")
    for function_name in function_names:
        logger.info(f"Invoking function: {function_name}")
        try:
            response = client.invoke(
                FunctionName=function_name.strip(), InvocationType="Event"
            )
            logger.info(f"Response from invoking {function_name}: {response}")
        except Exception as e:
            logger.error(f"Error invoking {function_name}: {str(e)}")

    continue_flag = index < count
    logger.info(f"Next index: {index}, Continue: {continue_flag}")

    return {"index": index, "continue": continue_flag, "count": count}
