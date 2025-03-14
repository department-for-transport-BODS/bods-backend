"""
Anti Virus Scan Exceptions
"""

from .exceptions_common import ETLException


class FileIOError(ETLException):
    """Base exception for antivirus scans."""

    code = "ANTIVIRUS_FAILURE"
    message_template = "Antivirus failed to read file."


class SuspiciousFile(ETLException):
    """
    Exception for when a suspicious file is found by the Anti-virus Scan
    """

    code = "SUSPICIOUS_FILE"
    message_template = "Anti-virus alert triggered for file {filename}."


class ClamConnectionError(ETLException):
    """Exception for when we can't connect to the ClamAV server."""

    code = "AV_CONNECTION_ERROR"
    message_template = "Could not connect to Clam daemon when \
                        testing {filename}."


class ClamAVScanFailed(ETLException):
    """
    Exception when a scan returns failed
    """

    code = "AV_CONNECTION_ERROR"
    message_template = "Could not connect to Clam daemon when \
                        testing {filename}."
