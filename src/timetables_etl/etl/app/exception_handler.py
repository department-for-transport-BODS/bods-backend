"""
Pipeline Exception Handler
"""

import traceback
from functools import wraps
from typing import Any, Dict

from structlog.stdlib import get_logger

from .database.repos.exceptions import DBBaseException

log = get_logger()


def handle_lambda_errors(func):
    """
    Lambda Error Handler
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            result = func(*args, **kwargs)
            return result
        except DBBaseException as e:
            log.error("Known error occurred", exc_info=True)
            return {
                "statusCode": 400,
                "body": {"error": {"code": e.error_code, "message": e.error_message}},
            }
        except Exception:
            log.error("Unexpected error occurred", exc_info=True)
            log.error(traceback.format_exc())
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
