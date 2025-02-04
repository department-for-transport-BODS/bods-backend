"""
Iterator Function that allows more granular execution of other Lambdas
"""

import time
from datetime import UTC, datetime
from os import environ
from typing import TYPE_CHECKING, Any

import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError, ParamValidationError
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

if TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient
log = get_logger()


def handle_interval(
    function_name: str,
    interval: int,
    current_minute_start: float,
    client: "LambdaClient",
) -> None:
    """
    Handles a single interval execution for the lambda function.
    """
    target_time = current_minute_start + interval
    wait_time = max(0, target_time - time.time())

    if wait_time > 0:
        log.info(
            "Sleeping for wait_time seconds to align with interval",
            wait_time=f"{wait_time:.2f}",
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
            "Synchronous invocation time in seconds", invoke_time=f"{invoke_time:.4f}"
        )
        log.info(
            "Response from Lambda Invoke",
            function_name=function_name,
            response=response["Payload"].read().decode(),
        )
    except (ClientError, ParamValidationError):
        log.error("Error invoking function", function_name=function_name, exc_info=True)


class MissingFunctionName(Exception):
    """
    functionName is Missing in the input
    """


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Executes the periodic tasks for sirivm/tfl/gtfsrt at 10s intervals.
    We need it because CW doesn't allow for more granular executions that 1min
    """
    configure_logging(event, context)
    client: LambdaClient = boto3.client(  # type: ignore
        "lambda", region_name=environ.get("AWS_REGION", "eu-west-2")
    )
    intervals: list[int] = event.get("intervals", [])
    function_name: str | None = event.get("functionName")

    if not function_name:
        log.error("No function name provided in the input!")
        return {"error": "functionName is required"}

    now = datetime.now(UTC)
    current_minute_start = time.mktime(now.timetuple())

    for interval in intervals:
        log.info("Actioning interval", interval=interval)
        handle_interval(function_name, interval, current_minute_start, client)

    return {
        "status": "completed",
        "executedIntervals": intervals,
        "functionName": function_name,
        "currentMinute": now.strftime("%Y-%m-%d %H:%M"),
    }
