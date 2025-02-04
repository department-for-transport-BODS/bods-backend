from .file_exceptions import ValidationException


# Exception for XML File processing
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


class FileNotXML(XMLValidationException):
    code = "FILE_NOT_XML_ERROR"
    message_template = "File {filename} is not a XML file."
