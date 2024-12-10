"""
Pipeline Exception Handler
"""

import traceback
from functools import wraps
from typing import Any

from structlog.stdlib import get_logger

log = get_logger()


class ETLException(Exception):
    """Base exception class for ETL operations"""

    def __init__(
        self,
        error_code: str,
        error_message: str,
        details: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.error_message = error_message
        self.details = details
        super().__init__(self.error_message)


def handle_lambda_errors(func):
    """
    Lambda Error Handler
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> dict[str, Any]:
        try:
            result = func(*args, **kwargs)
            return result
        except ETLException as e:
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
