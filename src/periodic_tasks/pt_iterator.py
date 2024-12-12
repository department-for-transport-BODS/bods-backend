import boto3
import logging
import time
from datetime import datetime
from os import environ
from sys import stdout

logger = logging.getLogger(__name__)
logger.setLevel(environ.get("LOG_LEVEL", "DEBUG"))
handler = logging.StreamHandler(stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

client = boto3.client("lambda")


def lambda_handler(event, context):
    intervals = event.get("intervals", [])
    function_name = event.get("functionName")
    if not function_name:
        logger.error("No function name provided in the input!")
        return {"error": "functionName is required"}

    now = datetime.utcnow()
    current_minute_start = time.mktime(now.timetuple())

    for interval in intervals:
        logger.info(f"Actioning interval: {interval}")
        target_time = current_minute_start + interval

        wait_time = max(0, target_time - time.time())
        if wait_time > 0:
            print(f"Sleeping for {wait_time:.2f} seconds to align with {interval} seconds.")
            time.sleep(wait_time)

        invoke_start = time.time()
        try:
            response = client.invoke(
                FunctionName=function_name.strip(),
                InvocationType="RequestResponse"
            )
            invoke_time = time.time() - invoke_start
            logger.info(f"Synchronous invocation time: {invoke_time:.4f} seconds")
            logger.info(f"Response from {function_name}: {response['Payload'].read().decode()}")
        except Exception as e:
            print(f"Error invoking {function_name}: {str(e)}")
            invoke_time = None

    return {
        "status": "completed",
        "executedIntervals": intervals,
        "functionName": function_name,
        "currentMinute": now.strftime("%Y-%m-%d %H:%M")
    }
