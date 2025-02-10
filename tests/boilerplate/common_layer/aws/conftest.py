"""
Fixtures  for AWS Tools
"""

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext


# pylint: disable=protected-access
@pytest.fixture(name="lambda_context")
def lambda_context_fixture() -> LambdaContext:
    """
    Lambda Context
    """
    context = LambdaContext()
    context._aws_request_id = "test-123"
    context._function_name = "test-function"
    context._log_group_name = "/aws/lambda/test"
    return context
