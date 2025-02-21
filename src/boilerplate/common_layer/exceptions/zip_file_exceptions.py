"""
Common exceptions for Zip Files
"""

from common_layer.database.models.model_pipelines import ETLErrorCode

from .file_exceptions import ValidationException


class NestedZipForbidden(ValidationException):
    """
    Exception for Nested Zips inside of Zip file
    """

    code = ETLErrorCode.NESTED_ZIP_FORBIDDEN
    message_template = "Zip file {filename} contains another zip file."


class ZipTooLarge(ValidationException):
    """
    Exception for Zip file exceeding maximum allowed size
    """

    code = ETLErrorCode.ZIP_TOO_LARGE
    message_template = "Zip file {filename} is too large."


class NoDataFound(ValidationException):
    """
    Exception for NoDataFound in Zip file
    """

    message_template = "Zip file {filename} contains no data files"
    code = ETLErrorCode.NO_DATA_FOUND
