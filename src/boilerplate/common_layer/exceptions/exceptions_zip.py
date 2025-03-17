"""
Common exceptions for Zip Files
"""

from common_layer.database.models import ETLErrorCode

from .exceptions_common import ETLException


class NestedZipForbidden(ETLException):
    """
    Exception for Nested Zips inside of Zip file
    """

    code = ETLErrorCode.NESTED_ZIP_FORBIDDEN


class ZipTooLarge(ETLException):
    """
    Exception for Zip file exceeding maximum allowed size
    """

    code = ETLErrorCode.ZIP_TOO_LARGE


class ZipNoDataFound(ETLException):
    """
    Exception for NoDataFound in Zip file
    """

    code = ETLErrorCode.NO_DATA_FOUND
