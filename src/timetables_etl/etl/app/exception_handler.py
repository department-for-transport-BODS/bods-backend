"""
Pipeline Exception Handler
"""

from functools import wraps
from typing import Any

from pydantic import ValidationError
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
    Lambda Error Handler with enhanced structured logging
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> dict[str, Any]:
        try:
            result = func(*args, **kwargs)
            return result
        except ETLException as e:
            log.error(
                "etl_error",
                error_type="known_error",
                error_code=e.error_code,
                error_message=e.error_message,
                function=func.__name__,
            )
            return {
                "statusCode": 400,
                "body": {"error": {"code": e.error_code, "message": e.error_message}},
            }
        except ValidationError as e:
            validation_errors = []
            for error in e.errors():
                validation_errors.append(
                    {
                        "field": error["loc"][-1],
                        "type": error["type"],
                        "msg": error["msg"],
                    }
                )

            log.error(
                "Pydantic Validation Error",
                error_type="validation_error",
                validation_errors=validation_errors,
                function=func.__name__,
            )
            return {
                "statusCode": 400,
                "body": {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Input validation failed",
                        "details": validation_errors,
                    }
                },
            }
        except Exception as e:
            log.error(
                "Unexpected Error",
                error_type="internal_error",
                error_class=e.__class__.__name__,
                error_message=str(e),
                function=func.__name__,
                exc_info=True,
            )
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
