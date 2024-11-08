"""
Description: Exception module for serverless bods
"""


class ValidationException(Exception):
    code = "VALIDATION_FAILED"
    message_template = "Validation failed for {filename}."

    def __init__(self, filename, line=1, message=None):
        self.filename = filename
        if message is None:
            self.message = self.message_template.format(filename=filename)
        else:
            self.message = message
        self.line = line


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


class NoSchemaDefinitionError(Exception):
    code = "NO_SCHEMA_FOUND"
    message_template = "No schema found for category {category}."

    def __init__(self, category, line=1, message=None):
        self.category = category
        if message is None:
            self.message = self.message_template.format(filename=category)
        else:
            self.message = message
        self.line = line


class NoDataFoundError(Exception):
    code = "NO_DATA_FOUND"
    message_template = "No data found for {field_name} {field_value}."

    def __init__(self, field_name, field_value, line=1, message=None):
        self.field_name = field_name
        self.field_value = field_value
        if message is None:
            self.message = self.message_template.format(
                field_name=field_name, field_value=field_value
            )
        else:
            self.message = message
        self.line = line


class XMLValidationException(ValidationException):
    code = "XML_VALIDATION_ERROR"
    message_template = "Unable to validate xml in {filename}."


class FileTooLarge(XMLValidationException):
    code = "FILE_TOO_LARGE"
    message_template = "XML file {filename} is too large."


class XMLSyntaxError(XMLValidationException):
    code = "XML_SYNTAX_ERROR"
    message_template = "File {filename} is not valid XML."
    line = ""


class DangerousXML(XMLValidationException):
    code = "DANGEROUS_XML_ERROR"
    message_template = "XML file {filename} contains dangerous XML."


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
