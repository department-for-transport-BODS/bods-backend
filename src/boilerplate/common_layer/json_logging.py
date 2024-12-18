"""
Structlog Config for JSON Logging Tailored for AWS
"""

import json
import logging
import sys
from typing import Any, Callable

import structlog
from structlog.processors import _json_fallback_handler
from structlog.types import EventDict


class AWSCloudWatchLogs:
    """
    Render a log line compatible with AWS CloudWatch Logs.
    AWS CloudWatch Logs allows for two space separated items before the json log
    Which makes reading them in the logs easier

    """

    def __init__(
        self,
        callouts: list | None = None,
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

        if isinstance(serialized, str):
            return prefix + serialized
        if isinstance(serialized, bytes):
            return prefix.encode() + serialized
        raise TypeError(f"Unexpected type from serializer: {type(serialized)}")


_NOISY_LOG_SOURCES = (
    "boto",
    "boto3",
    "botocore",
    "urllib3",
    "s3transfer",
    "aws_xray_sdk",
)
_PROCESSORS = (
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
    structlog.threadlocal.merge_threadlocal,
    AWSCloudWatchLogs(callouts=["event", "func_name"]),
)


def configure_logging():
    """
    Configure Structured JSON logging for the application
    Import and run this as the first thing in a lambda function
    """

    # Structlog configuration
    structlog.configure(
        processors=list(_PROCESSORS),
        context_class=dict,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # reset the AWS-Lambda-supplied log handlers.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG,
        force=True,
    )
    for source in _NOISY_LOG_SOURCES:
        logging.getLogger(source).setLevel(logging.WARNING)
