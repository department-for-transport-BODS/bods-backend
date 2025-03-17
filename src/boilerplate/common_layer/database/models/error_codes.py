"""
ETL Error Codes
"""

from enum import Enum


class ETLErrorCode(str, Enum):
    """Error codes for ETL tasks"""

    # General
    SYSTEM_ERROR = "An unknown error occurred in the ETL process."
    EMPTY = ""

    # Anti Virus
    AV_SUSPICIOUS_FILE = "Suspicious file detected."
    AV_FILE_IO = "Antivirus failed to read file"
    AV_CONNECTION_ERROR = "Connection to antivirus service failed."
    AV_SCAN_FAILED = "Antivirus Service Reported Scan Failed"

    # S3
    S3_FILENAME_PARSE_FAIL = "Could not extract filename from ObjectKey"
    S3_OBJECT_TOO_LARGE = "S3 File Exceeds Maximum Allowed Size"

    # File Download
    DOWNLOAD_EXCEPTION = "General File Download Exception"
    DOWNLOAD_TIMEOUT = "File Download Timed Out"
    DOWNLOAD_PERMISSION_DENIED = "File Download HTTP 403 Permission Denied"
    DOWNLOAD_NOT_FOUND = "File Download HTTP 404 Not Found"
    DOWNLOAD_UNKNOWN_FILE_TYPE = "File Downloaded is not .xml or .zip"

    # File Validation
    FILE_TOO_LARGE = "XML file is too large."
    ZIP_TOO_LARGE = "Zip file is too large."
    NESTED_ZIP_FORBIDDEN = "Zip file contains one or more zip file(s)."
    NO_DATA_FOUND = "Zip file contains no XML files."
    NO_VALID_FILE_TO_PROCESS = "No valid file to process."

    # XML
    XML_SYNTAX_ERROR = "XML syntax error."
    XML_FILE_NOT_XML = "Input file is not an XML"
    XML_DANGEROUS_CONTENT_FOUND = "Dangerous XML content detected."

    # Schema
    SCHEMA_ERROR = "XSD Schema Validation error."
    SCHEMA_VERSION_MISSING = "Schema version is missing."
    SCHEMA_VERSION_NOT_SUPPORTED = "Schema version is not supported."

    # Post Schema
    POST_SCHEMA_ERROR = "Post-schema validation error."
    DATASET_EXPIRED = "Dataset has expired."

    @property
    def code(self) -> str:
        """Return the enum name (to use as the error code)"""
        return self.name
