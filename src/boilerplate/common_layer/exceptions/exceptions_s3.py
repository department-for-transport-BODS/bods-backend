"""
Custom S3 Exceptions
"""

from common_layer.database.models import ETLErrorCode

from .exceptions_common import ETLException


class S3FilenameParseFailed(ETLException):
    """
    If the S3 object key extraction failed
    """

    code = ETLErrorCode.S3_FILENAME_PARSE_FAIL


class S3FileTooLargeError(ETLException):
    """Raised when file size exceeds maximum allowed size"""

    code = ETLErrorCode.S3_OBJECT_TOO_LARGE
