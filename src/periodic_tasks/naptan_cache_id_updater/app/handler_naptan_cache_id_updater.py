from typing import Any

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

tracer = Tracer()
log = get_logger()


@tracer.capture_lambda_handler
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for updating Naptan Stop Points in DynamoDB with IDs from the BODs DB
    """
    configure_logging(event, context)

    response = {
        "statusCode": 200,
        "body": {
            "message": "Successfully updated NaPTAN StopPoint IDs",
        },
    }

    return response
