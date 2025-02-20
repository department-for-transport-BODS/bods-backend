"""
ClamAV Scanner Lambda Exception
"""


class S3FileTooLargeError(Exception):
    """Raised when file size exceeds maximum allowed size"""
