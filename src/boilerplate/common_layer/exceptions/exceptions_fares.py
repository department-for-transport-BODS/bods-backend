"""
Fares Exceptions
"""

from common_layer.database.models import ETLErrorCode

from .exceptions_common import ETLException


class FaresMetadataNotFound(ETLException):
    """
    Fares Metadata not found in DynamoDB for aggregation
    """

    code = ETLErrorCode.NO_VALID_FILE_TO_PROCESS
