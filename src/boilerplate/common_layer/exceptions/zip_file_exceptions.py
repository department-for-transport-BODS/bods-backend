from .file_exceptions import ValidationException


# Exception for Zip File processing
class ZipValidationException(ValidationException):
    code = "ZIP_VALIDATION_FAILED"
    message_template = "Unable to validate zip {filename}."


class NestedZipForbidden(ZipValidationException):
    code = "NESTED_ZIP_FORBIDDEN"
    message_template = "Zip file {filename} contains another zip file."


class ZipTooLarge(ZipValidationException):
    code = "ZIP_TOO_LARGE"
    message_template = "Zip file {filename} is too large."


class NoDataFound(ZipValidationException):
    message_template = "Zip file {filename} contains no data files"
    code = "NO_DATA_FOUND"
