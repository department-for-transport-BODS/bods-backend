"""
Lambda: CollateFiles
"""

import json

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Lambda Handler for CollateFiles
    """
    return {"statusCode": 200, "body": json.dumps(event)}
