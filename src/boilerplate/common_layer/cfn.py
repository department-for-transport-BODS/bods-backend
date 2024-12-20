"""
Cloudformation Response Decorator
When using a lambda as part of a cloudformation custom resource
The result of the execution needs to be sent to the platform
"""

import functools
import json
from typing import Any, Callable

import urllib3
from structlog.stdlib import get_logger

logger = get_logger()
http = urllib3.PoolManager()


def cloudformation_response(
    success_status_code: int = 200, error_status_code: int = 400
) -> Callable:
    """
    Decorator to handle both CloudFormation custom resource responses and direct Lambda invocations.

    When using a custom resource to call a lambda as part of a SAM template,
    it will hang unless you send the results to the CFN API Server.
    For direct Lambda invocations, it will log a warning and proceed normally.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
            # Check if this is a CloudFormation custom resource call
            is_cloudformation = all(
                key in event
                for key in ["StackId", "RequestId", "LogicalResourceId", "ResponseURL"]
            )

            if not is_cloudformation:
                logger.warning(
                    "Direct Lambda invocation detected - skipping CloudFormation response",
                    event_type="direct_invocation",
                )
                return func(event, context)

            def send_response(status: str, data: dict[str, Any] | None = None) -> None:
                response_body = {
                    "Status": status,
                    "Reason": "See CloudWatch logs for details",
                    "PhysicalResourceId": context.log_stream_name,
                    "StackId": event["StackId"],
                    "RequestId": event["RequestId"],
                    "LogicalResourceId": event["LogicalResourceId"],
                    "Data": data or {},
                }

                logger.info("Sending Cloudformation Result", **response_body)
                response_url = event["ResponseURL"]

                try:
                    json_response_body = json.dumps(response_body)
                    headers = {
                        "content-type": "",
                        "content-length": str(len(json_response_body)),
                    }

                    response = http.request(
                        "PUT",
                        response_url,
                        body=json_response_body.encode("utf-8"),
                        headers=headers,
                    )

                    logger.info(
                        "Sent Cloud Formation Result",
                        status_code=response.status,
                        response_url=response_url,
                    )

                except Exception as e:
                    logger.error(
                        "Failed to Send CFN Result",
                        error=str(e),
                        response_url=response_url,
                    )
                    raise

            try:
                # Handle Delete events automatically
                if is_cloudformation and event["RequestType"] == "Delete":
                    logger.info("Processing Delete Event (Dummy Success)")
                    send_response("SUCCESS")
                    return {
                        "statusCode": success_status_code,
                        "body": "Nothing to delete",
                    }

                # For Create/Update events or direct invocations, execute the wrapped function
                if not is_cloudformation or event["RequestType"] in [
                    "Create",
                    "Update",
                ]:
                    result = func(event, context)
                    if is_cloudformation:
                        send_response("SUCCESS", result.get("data"))
                    return {
                        "statusCode": success_status_code,
                        "body": result.get(
                            "message", "Operation completed successfully"
                        ),
                    }

                # Handle unsupported request types (only for CloudFormation)
                msg = f"Unsupported request type: {event['RequestType']}"
                logger.error(
                    "Unsupported request type", request_type=event["RequestType"]
                )
                send_response("FAILED", {"Error": msg})
                return {"statusCode": error_status_code, "body": msg}

            except Exception as e:
                error_message = str(e)
                logger.error("operation_failed", error=error_message)
                if is_cloudformation:
                    send_response("FAILED", {"Error": error_message})
                raise

        return wrapper

    return decorator
