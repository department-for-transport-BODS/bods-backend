"""
Exception Exports
"""

from .exceptions_anti_virus import ClamAVScanFailed, ClamConnectionError, SuspiciousFile
from .exceptions_common import ETLException
from .exceptions_download import (
    DownloadException,
    DownloadFileNotFound,
    DownloadPermissionDenied,
    DownloadProxyError,
    DownloadTimeout,
    DownloadUnknownFileType,
)
from .exceptions_fares import FaresMetadataNotFound
from .exceptions_pti import PTIViolationFound
from .exceptions_s3 import S3FilenameParseFailed, S3FileTooLargeError
from .exceptions_schema import (
    PostSchemaViolationsFound,
    SchemaMismatch,
    SchemaUnknown,
    SchemaViolationsFound,
)
from .exceptions_xml import DangerousXML, FileNotXML, XMLSyntaxError
from .exceptions_zip import NestedZipForbidden, ZipNoDataFound, ZipTooLarge

__all__ = [
    # Common
    "ETLException",
    # Anti-virus exceptions
    "ClamAVScanFailed",
    "ClamConnectionError",
    "SuspiciousFile",
    # Download exceptions
    "DownloadException",
    "DownloadTimeout",
    "DownloadPermissionDenied",
    "DownloadUnknownFileType",
    "DownloadFileNotFound",
    "DownloadProxyError",
    # S3 exceptions
    "S3FilenameParseFailed",
    "S3FileTooLargeError",
    # Schema
    "SchemaViolationsFound",
    "PostSchemaViolationsFound",
    "SchemaUnknown",
    "SchemaMismatch",
    # XML exceptions
    "DangerousXML",
    "FileNotXML",
    "XMLSyntaxError",
    # ZIP exceptions
    "NestedZipForbidden",
    "ZipNoDataFound",
    "ZipTooLarge",
    # PTI
    "PTIViolationFound",
    # Fares
    "FaresMetadataNotFound",
]
