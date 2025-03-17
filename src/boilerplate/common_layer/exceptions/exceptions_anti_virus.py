"""
Anti Virus Scan Exceptions
"""

from common_layer.database.models import ETLErrorCode

from .exceptions_common import ETLException


class FileIOError(ETLException):
    """Base exception for antivirus scans."""

    code = ETLErrorCode.AV_FILE_IO


class SuspiciousFile(ETLException):
    """
    Exception for when a suspicious file is found by the Anti-virus Scan
    """

    code = ETLErrorCode.SUSPICIOUS_FILE


class ClamConnectionError(ETLException):
    """Exception for when we can't connect to the ClamAV server."""

    code = ETLErrorCode.AV_CONNECTION_ERROR


class ClamAVScanFailed(ETLException):
    """
    Exception when a scan returns failed
    """

    code = ETLErrorCode.AV_SCAN_FAILED
