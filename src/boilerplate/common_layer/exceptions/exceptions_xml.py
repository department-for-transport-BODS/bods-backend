"""
XML Exceptions
"""

from common_layer.database.models import ETLErrorCode

from .exceptions_common import ETLException


class XMLSyntaxError(ETLException):
    """
    Syntax error
    """

    code = ETLErrorCode.XML_SYNTAX_ERROR


class DangerousXML(ETLException):
    """
    Defused XML Failed
    """

    code = ETLErrorCode.XML_DANGEROUS_CONTENT_FOUND


class FileNotXML(ETLException):
    """
    File is not XML
    """

    code = ETLErrorCode.XML_FILE_NOT_XML
