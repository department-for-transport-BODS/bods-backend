"""
PlaceholderLambda
"""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from structlog.stdlib import get_logger

log = get_logger()


def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Main lambda handler
    """
    log.info("Placeholder Lambda - No functionality")

    return {"statusCode": 200, "body": "Successfully ran the placeholder lambda"}
