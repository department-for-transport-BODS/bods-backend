"""
Exceptions for Schema Checks
"""

from common_layer.database.models import ETLErrorCode

from .exceptions_common import ETLException


class SchemaViolationsFound(ETLException):
    """
    Exception raised when schema violation is found
    """

    code = ETLErrorCode.SCHEMA_ERROR


class PostSchemaViolationsFound(ETLException):
    """
    Exception raised when schema violation is found
    """

    code = ETLErrorCode.POST_SCHEMA_ERROR
