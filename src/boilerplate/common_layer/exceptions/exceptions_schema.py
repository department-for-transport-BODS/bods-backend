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


class SchemaUnknown(ETLException):
    """
    Exception raised when input XML is an unknown type
    """

    code = ETLErrorCode.SCHEMA_UNKNOWN


class SchemaMismatch(ETLException):
    """
    Exception raised when input XML does not match requested data type
    """

    code = ETLErrorCode.SCHEMA_MISMATCH


class PostSchemaViolationsFound(ETLException):
    """
    Exception raised when schema violation is found
    """

    code = ETLErrorCode.POST_SCHEMA_ERROR
