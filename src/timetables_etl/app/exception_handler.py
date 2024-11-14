"""
Pipeline Exception Handler
"""

import traceback
from functools import wraps
from typing import Any, Dict

from logger import logger

from .database.repos.exceptions import DBBaseException


class InvalidXMLException(DBBaseException):
    """Raised when XML parsing fails"""

    error_code = "INVALID_XML"
    error_message = "Failed to parse XML data"


def handle_lambda_errors(func):
    """
    Lambda Error Handler
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            return {"statusCode": 200, "body": func(*args, **kwargs)}
        except DBBaseException as e:
            logger.error("Known error occurred", exc_info=True)
            return {
                "statusCode": 400,
                "body": {"error": {"code": e.error_code, "message": e.error_message}},
            }
        except Exception:
            logger.error("Unexpected error occurred", exc_info=True)
            logger.error(traceback.format_exc())
            return {
                "statusCode": 500,
                "body": {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                    }
                },
            }

    return wrapper
