"""
Periodic Task Iterator Lambda
"""

import time
from datetime import UTC, datetime
from os import environ
from typing import Any

import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

log = get_logger()

client = boto3.client("lambda", region_name=environ.get("AWS_REGION", "eu-west-2"))  # type: ignore


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handler for iterating through and invoking periodic tasks
    """
    configure_logging(event, context)
    intervals = event.get("intervals", [])
    function_name = event.get("functionName")
    if not function_name:
        log.error("No function name provided in the input!")
        return {"error": "functionName is required"}

    now = datetime.now(UTC)
    current_minute_start = time.mktime(now.timetuple())

    for interval in intervals:
        log.info("Actioning interval", interval=interval)
        target_time = current_minute_start + interval

        wait_time = max(0, target_time - time.time())
        if wait_time > 0:
            log.info(
                "Sleeping for wait_time to align with interval seconds.",
                wait_time=wait_time,
                interval=interval,
            )
            time.sleep(wait_time)

        invoke_start = time.time()
        try:
            response = client.invoke(
                FunctionName=function_name.strip(), InvocationType="RequestResponse"
            )
            invoke_time = time.time() - invoke_start
            log.info(
                "Synchronous invocation time",
                invoke_time=invoke_time,
            )
            log.info(
                "Response received from function",
                function_name=function_name,
                response=response["Payload"].read().decode(),
            )
        except Exception:  # pylint: disable=broad-exception-caught
            log.error(
                "Error invoking function",
                function_name=function_name,
                exc_info=True,
            )
            invoke_time = None

    return {
        "status": "completed",
        "executedIntervals": intervals,
        "functionName": function_name,
        "currentMinute": now.strftime("%Y-%m-%d %H:%M"),
    }
