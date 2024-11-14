"""
Parse Operators TXC XML 
"""

from typing import cast, get_args

from lxml.etree import _Element
from structlog.stdlib import get_logger

from ..models.txc_operator import TXCOperator
from ..models.txc_types import LicenceClassificationT, TransportModeType
from .utils import find_section
from .utils_tags import get_element_text

log = get_logger()


def parse_transport_mode(operator_xml: _Element) -> TransportModeType:
    """
    Return transport mode
    """
    primary_mode = get_element_text(operator_xml, "PrimaryMode")
    if primary_mode in get_args(TransportModeType):
        return cast(TransportModeType, primary_mode)
    return "coach"


def parse_licence_classification(
    operator_xml: _Element,
) -> LicenceClassificationT | None:
    """
    Return licence classicifcation
    """
    primary_mode = get_element_text(operator_xml, "LicenceClassification")
    if primary_mode in get_args(LicenceClassificationT):
        return cast(LicenceClassificationT, primary_mode)
    return None


def parse_operator(operator_xml: _Element) -> TXCOperator | None:
    """
    Parse Operators -> Operator
    Licenced Operators are not allowedin PTI so convert to Operator
    PTI 1.1A Page 27 Section 4.2
    """
    national_operator_code = get_element_text(operator_xml, "NationalOperatorCode")
    operator_short_name = get_element_text(operator_xml, "OperatorShortName")
    trading_name = get_element_text(operator_xml, "TradingName")
    licence_number = get_element_text(operator_xml, "LicenceNumber")

    primary_mode: TransportModeType = parse_transport_mode(operator_xml)
    licence_classification: LicenceClassificationT | None = (
        parse_licence_classification(operator_xml)
    )
    if not national_operator_code or not operator_short_name:
        log.warning(
            "Operator missing required fields. Skipping.",
            NationalOperatorCode=national_operator_code,
            OperatorShortName=operator_short_name,
        )
        return None

    operator = TXCOperator(
        NationalOperatorCode=national_operator_code,
        OperatorShortName=operator_short_name,
        TradingName=trading_name,
        LicenceNumber=licence_number,
        PrimaryMode=primary_mode,
        OperatorNameOnLicence=get_element_text(operator_xml, "OperatorNameOnLicence"),
        LicenceClassification=licence_classification,
    )
    return operator


def parse_operators(xml_data: _Element) -> list[TXCOperator]:
    """
    Operators Section
    """
    section = find_section(xml_data, "Operators")
    if section is None:
        log.warning("No Operators Found")
        return []

    operator_parsers = {
        "Operator": parse_operator,
        "LicensedOperator": parse_operator,
    }

    operators = []
    for operator_xml in section.findall("*"):
        parser = operator_parsers.get(operator_xml.tag)
        if parser:
            try:
                operator = parser(operator_xml)
                if operator:
                    operators.append(operator)
            except ValueError:
                log.warning("Value error when parsing Operator", exc_info=True)
        else:
            log.warning("Unknown operator type. Skipping.", tag=operator_xml.tag)

    return operators
