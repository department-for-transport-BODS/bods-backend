"""
Exceptions for Schema Checks
"""

from .exceptions_common import ETLException


class SchemaViolationsFound(ETLException):
    """
    Exception raised when schema violation is found
    """

    code = "SCHEMA_ERROR"
    message_template = "Found XSD Schema Violations"


class PostSchemaViolationsFound(ETLException):
    """
    Exception raised when schema violation is found
    """

    code = "POST_SCHEMA_ERROR"
    message_template = "Found Post Schema Violations"
