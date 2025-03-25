"""
Fares Exceptions
"""

from common_layer.database.models import ETLErrorCode

from .exceptions_common import ETLException


class FaresMetadataNotFound(ETLException):
    """
    Fares Metadata not from in DynamoDB for aggregation
    """

    code = ETLErrorCode.FARES_METADATA_NOT_FOUND
