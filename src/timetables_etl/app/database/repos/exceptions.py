"""
Lambda Exceptions
"""


class DBBaseException(Exception):
    """Base exception for Lambda errors"""

    error_code: str = "UNKNOWN_ERROR"
    error_message: str = "An unknown error occurred"


class TaskNotFoundException(DBBaseException):
    """Raised when an ETL task is not found"""

    error_code = "TASK_NOT_FOUND"
    error_message = "ETL task not found"


class RevisionNotFoundException(DBBaseException):
    """Raised when an ETL task is not found"""

    error_code = "REVISION_NOT_FOUND"
    error_message = "Revision not found in database"
