"""
XML Checks
"""

from io import BytesIO
from xml.etree.ElementTree import ElementTree, ParseError

from common_layer.exceptions.xml_file_exceptions import (
    DangerousXML,
    FileNotXML,
    XMLSyntaxError,
)
from defusedxml import DefusedXmlException
from defusedxml import ElementTree as detree
from structlog.stdlib import get_logger

log = get_logger()


def dangerous_xml_check(file_object: BytesIO, file_name: str) -> ElementTree:
    """
    Parse and check the file object syntax error
    Uses defusedxml to parse XML to check for common XML issues
        e.g.
            - Entity Expansion,
            - External Entity (XXE)
    We also are disallowing Document Type Definitions
    """
    try:
        parsed_xml = detree.parse(
            file_object, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
        log.info(
            "XML successfully validated with no dangerous content",
        )
        return parsed_xml
    except (detree.ParseError, ParseError) as err:
        error_message = str(err)
        log.error("XML syntax error", error_message=error_message)
        raise XMLSyntaxError(file_name, message=err.msg) from err
    except DefusedXmlException as err:
        log.error("Dangerous XML", exc_info=True)
        raise DangerousXML(file_name, message=err) from err


def validate_is_xml_file(file_name: str) -> None:
    """
    Check file extension ends in .xml
    """
    if not file_name.lower().endswith(".xml"):
        log.error("File is not a xml file", file_name=file_name)
        raise FileNotXML(file_name)
