"""
Exception for File Processing
"""

from common_layer.database.models import ETLErrorCode

from .exceptions_common import ETLException


class DownloadException(ETLException):
    """
    General Download Error
    """

    code = ETLErrorCode.DOWNLOAD_EXCEPTION


class DownloadTimeout(ETLException):
    """A request timed out."""

    code = ETLErrorCode.DOWNLOAD_TIMEOUT


class PermissionDenied(ETLException):
    """A permission denied response was received."""

    code = ETLErrorCode.DOWNLOAD_PERMISSION_DENIED


class FileNotFound(ETLException):
    """A permission denied response was received."""

    code = ETLErrorCode.DOWNLOAD_NOT_FOUND


class UnknownFileType(ETLException):
    """The content returned in the response was of an unknown file type."""

    code = ETLErrorCode.DOWNLOAD_UNKNOWN_FILE_TYPE
