"""
Exception for File Processing
"""


class ValidationException(Exception):
    """
    This exception is intended to be used when a validation operation fails.
    """

    code = "VALIDATION_FAILED"
    message_template = "Validation failed for {filename}."

    def __init__(self, filename, line=1, message=None):
        self.filename = filename
        if message is None:
            self.message = self.message_template.format(filename=filename)
        else:
            self.message = message
        self.line = line

    def __str__(self):
        return (
            f"[{self.code}] {self.message} "
            f"(File: {self.filename}, Line: {self.line})"
        )


class AntiVirusError(ValidationException):
    """Base exception for antivirus scans."""

    code = "ANTIVIRUS_FAILURE"
    message_template = "Antivirus failed validating file {filename}."


class SuspiciousFile(AntiVirusError):
    """Exception for when a suspicious file is found."""

    code = "SUSPICIOUS_FILE"
    message_template = "Anti-virus alert triggered for file {filename}."


class ClamConnectionError(AntiVirusError):
    """Exception for when we can't connect to the ClamAV server."""

    code = "AV_CONNECTION_ERROR"
    message_template = "Could not connect to Clam daemon when \
                        testing {filename}."


class DownloadException(Exception):
    """An ambigious exception occurred during the request.

    Args:
        url (str): The url that was being accessed.
    """

    code = "DOWNLOAD_EXCEPTION"
    message_template = "Unable to download data from {url}."

    def __init__(self, url, message=None):
        self.url = url
        if message is None:
            self.message = self.message_template.format(url=url)
        else:
            self.message = message


class DownloadTimeout(DownloadException):
    """A request timed out."""

    code = "DOWNLOAD_TIMEOUT"
    message_template = "Request to {url} timed out."


class PermissionDenied(DownloadException):
    """A permission denied response was received."""

    code = "PERMISSION_DENIED"
    message_template = "Permission to access {url} denied."


class UnknownFileType(DownloadException):
    """The content returned in the response was of an unknown file type."""

    code = "UNKNOWN_FILE_TYPE"
    message_template = "File downloaded from {url} is not a zip or xml"
