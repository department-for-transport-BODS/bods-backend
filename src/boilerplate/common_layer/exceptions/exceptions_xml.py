"""
XML Exceptions
"""

from .exceptions_common import ETLException


class XMLSyntaxError(ETLException):
    """
    Syntax error
    """

    code = "XML_SYNTAX_ERROR"
    message_template = "File is not valid XML."


class DangerousXML(ETLException):
    """
    Defused XML Failed
    """

    code = "DANGEROUS_XML_ERROR"
    message_template = "XML file contains dangerous XML."


class FileNotXML(ETLException):
    """
    File is not XML
    """

    code = "FILE_NOT_XML_ERROR"
    message_template = "File is not a XML file."
