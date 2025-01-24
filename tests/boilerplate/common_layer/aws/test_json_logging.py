"""
Test JSON Log Setup
"""

import json
import logging
import sys

import pytest
import structlog
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.json_logging import (
    _NOISY_LOG_SOURCES,
    AWSCloudWatchLogs,
    configure_logging,
    get_processors,
)


# pylint: disable=protected-access
@pytest.fixture(name="lambda_context")
def lambda_context_fixture():
    """
    Lambda Context
    """
    context = LambdaContext()
    context._aws_request_id = "test-123"
    context._function_name = "test-function"
    context._log_group_name = "/aws/lambda/test"
    return context


@pytest.mark.parametrize(
    "context, expected_keys",
    [
        pytest.param(None, ["timestamp", "level", "event"], id="No Lambda Context"),
        pytest.param(
            "use_fixture",
            ["timestamp", "level", "event", "requestId"],
            id="With Lambda Context",
        ),
    ],
)
def test_get_processors_output(context, expected_keys, lambda_context, capsys):
    """
    Tests CloudWatch log formatting.

    Format: [LEVEL] "callout1" "callout2" {...json payload...}
    Example: [INFO] "test" "func_name" {"event": "test", "level": "info", "requestId": "123"}

    CloudWatch parses this for easy querying via Logs Insights.
    """
    if context == "use_fixture":
        context = lambda_context

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
        force=True,
    )

    structlog.configure(
        processors=get_processors(context),
        context_class=dict,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logger = structlog.getLogger()
    logger.info("test")

    captured = capsys.readouterr()
    json_str = captured.out.split('"test_get_processors_output" ')[1]
    output = json.loads(json_str)
    assert all(key in output for key in expected_keys)


def test_cloudwatch_logs_formatting():
    """
    Tests AWS CloudWatch log format follows pattern:
        [LEVEL] "callout1" "callout2" {...json...}
    """
    renderer = AWSCloudWatchLogs(callouts=["event", "other"])
    event_dict = {"event": "test", "other": "value"}
    result = renderer(None, "INFO", event_dict)
    expected_prefix = '[INFO] "test" "value"'
    assert result[: len(expected_prefix)] == expected_prefix


def test_noisy_loggers_level():
    """
    Tests boto3 and other AWS SDK loggers are set to WARNING level
    """
    configure_logging()
    for source in _NOISY_LOG_SOURCES:
        assert logging.getLogger(source).level == logging.WARNING
