"""
Custom S3 Exceptions
"""

from .exceptions_common import ETLException


class S3FilenameParseFailed(ETLException):
    """
    If the S3 object key extraction failed
    """

    code = "S3_ERROR"
    message_template = "Could not extract filename from s3_file_key"


class S3FileTooLargeError(ETLException):
    """Raised when file size exceeds maximum allowed size"""

    code = "S3_ERROR"
    message_template = "S3 File exceeds maximum allowed size"
