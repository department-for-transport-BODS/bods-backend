"""
Structlog Config for JSON Logging Tailored for AWS
"""

import json
import logging
import os
import sys
from typing import Any, Callable

import structlog
from aws_lambda_powertools.utilities.typing import LambdaContext
from structlog.processors import _json_fallback_handler  # type: ignore
from structlog.types import EventDict
from structlog.typing import Processor


class RequestIdProcessor:
    """
    Processor that adds AWS Lambda request ID to structured logging events.
    Follows AWS Lambda log format by using 'requestId' as the key.
    """

    def __init__(self, request_id: str | None = None) -> None:
        self._request_id = request_id

    def __call__(
        self,
        logger: Any,
        method_name: str,
        event_dict: EventDict,
    ) -> EventDict:
        """
        Add requestId to the event dict if available.
        """
        if self._request_id is not None:
            event_dict["requestId"] = self._request_id
        return event_dict


class AWSCloudWatchLogs:
    """
    Render a log line compatible with AWS CloudWatch Logs.
    AWS CloudWatch Logs allows for two space separated items before the json log
    Which makes reading them in the logs easier

    """

    def __init__(
        self,
        callouts: list[str] | None = None,
        serializer: Callable[..., str | bytes] = json.dumps,
        **dumps_kw: Any,
    ) -> None:
        if callouts is None:
            callouts = []
        self._callout_one_key = callouts[0] if len(callouts) > 0 else None
        self._callout_two_key = callouts[1] if len(callouts) > 1 else None
        dumps_kw.setdefault("default", _json_fallback_handler)
        self._dumps_kw = dumps_kw
        self._dumps = serializer

    def __call__(self, _, name: str, event_dict: EventDict) -> str | bytes:
        callout_one = (
            event_dict.get(self._callout_one_key, "")
            if self._callout_one_key
            else "none"
        )
        callout_two = (
            event_dict.get(self._callout_two_key, "")
            if self._callout_two_key
            else "none"
        )

        prefix = f'[{name.upper()}] "{callout_one}" "{callout_two}" '
        serialized = self._dumps(event_dict, **self._dumps_kw)

        match serialized:
            case str():
                return prefix + serialized
            case bytes():
                return prefix.encode() + serialized
            case _:
                raise TypeError(f"Unexpected type from serializer: {type(serialized)}")


_NOISY_LOG_SOURCES = (
    "boto",
    "boto3",
    "botocore",
    "urllib3",
    "s3transfer",
    "aws_xray_sdk",
    "ddtrace",
)


def get_log_level() -> int:
    """
    Get the log level from environment variable or use DEBUG as default.
    Valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    log_level_str = os.environ.get("LOG_LEVEL", "DEBUG").upper()

    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level_int = log_level_map.get(log_level_str, logging.DEBUG)
    logger = structlog.stdlib.get_logger()
    logger.info(
        "Logging Configured", log_level_int=log_level_int, log_level_str=log_level_str
    )
    return log_level_int


def get_processors(
    lambda_context: LambdaContext | None = None,
) -> tuple[Processor, ...]:
    """
    Get the list of processors, optionally including request ID processor
    """
    base_processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FUNC_NAME,
            }
        ),
        structlog.contextvars.merge_contextvars,
    ]

    if lambda_context:
        base_processors.append(RequestIdProcessor(lambda_context.aws_request_id))

    base_processors.append(AWSCloudWatchLogs(callouts=["event", "func_name"]))
    return tuple(base_processors)


def configure_logging(
    event_dict: dict[str, Any] | None = None,
    lambda_context: LambdaContext | None = None,
):
    """
    Configure Structured JSON logging for the application
    Import and run this as the first thing in a lambda function

    The log level can be set using the LOG_LEVEL environment variable
    Valid values are: DEBUG, INFO, WARNING, WARN, ERROR, CRITICAL
    Defaults to DEBUG if not specified or invalid
    """
    processors = get_processors(lambda_context)
    # Structlog configuration
    structlog.configure(
        processors=list(processors),
        context_class=dict,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    if event_dict:
        structlog.contextvars.bind_contextvars(**event_dict)

    log_level = get_log_level()

    # reset the AWS-Lambda-supplied log handlers.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )
    for source in _NOISY_LOG_SOURCES:
        logging.getLogger(source).setLevel(logging.WARNING)
