"""
PlaceholderLambda
"""

from structlog.stdlib import get_logger

log = get_logger()


def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Main lambda handler
    """

    return {
        "statusCode": 200,
        "body": "Successfully ran the placeholder check"
    }
