"""
Parse Operators TXC XML
"""

from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import find_section, get_element_text, get_tag_str
from ..models import LicenceClassificationT, TransportModeT, TXCOperator

log = get_logger()


def parse_transport_mode(operator_xml: _Element) -> TransportModeT:
    """
    Return transport mode
    Defaults to bus
    """
    primary_mode = get_element_text(operator_xml, "PrimaryMode")
    if primary_mode in get_args(TransportModeT):
        return cast(TransportModeT, primary_mode)
    return "bus"


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

    primary_mode: TransportModeT = parse_transport_mode(operator_xml)
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
    try:
        section = find_section(xml_data, "Operators")
    except ValueError:
        log.warning("No Operators Found")
        return []

    operator_parsers = {
        "Operator": parse_operator,
        "LicensedOperator": parse_operator,
    }

    operators: list[TXCOperator] = []
    for operator_xml in section.findall("*"):
        tag_name = get_tag_str(operator_xml)
        if tag_name is None:
            log.warning("Unknown operator type. Skipping.", tag=operator_xml.tag)
            continue
        parser = operator_parsers.get(tag_name)
        if parser:
            try:
                operator = parser(operator_xml)
                if operator:
                    operators.append(operator)
            except ValueError:
                log.warning("Value error when parsing Operator", exc_info=True)
        else:
            log.warning("Unknown operator type. Skipping.", tag=operator_xml.tag)
    log.info("Parsed TXC Operators", count=len(operators))
    return operators
