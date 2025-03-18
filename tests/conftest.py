"""
Pytest Global Conftest
"""

import os

import pytest

from .fixtures.context import mocked_context


# Mock decorator to that returns the original function
def decorator_mock(step_name):
    def wrapper(func):
        return func

    return wrapper


@pytest.fixture(scope="session", autouse=True)
def set_metrics_env():
    """
    Cloudwatch metrics requires these env vars to be set
    """
    os.environ["POWERTOOLS_METRICS_NAMESPACE"] = "pytest-namesapce"
    os.environ["POWERTOOLS_SERVICE_NAME"] = "pytest-service"