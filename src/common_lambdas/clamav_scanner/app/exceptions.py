"""
ClamAV Scanner Lambda Exception
"""


class S3FileTooLargeError(Exception):
    """Raised when file size exceeds maximum allowed size"""


class NestedZipForbidden(Exception):
    """Raised when file size exceeds maximum allowed size"""


class ZipTooLarge(Exception):
    """
    Raised when the Zip File Contents are too large uncompressed
    """
