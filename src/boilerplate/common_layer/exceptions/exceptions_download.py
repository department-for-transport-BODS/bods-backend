"""
Exception for File Processing
"""

from .exceptions_common import ETLException


class DownloadException(ETLException):
    """
    General Download Error
    """

    code = "DOWNLOAD_EXCEPTION"
    message_template = "Unable to download data."


class DownloadTimeout(ETLException):
    """A request timed out."""

    code = "DOWNLOAD_TIMEOUT"
    message_template = "Request timed out"


class PermissionDenied(ETLException):
    """A permission denied response was received."""

    code = "PERMISSION_DENIED"
    message_template = "Access denied for file"


class UnknownFileType(ETLException):
    """The content returned in the response was of an unknown file type."""

    code = "UNKNOWN_FILE_TYPE"
    message_template = "File downloaded is not a zip or xml"
