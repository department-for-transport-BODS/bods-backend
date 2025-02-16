"""
Tariff Parsing
"""

from lxml.etree import _Element
from structlog.stdlib import get_logger

from ...models import Tariff
from ..netex_utility import (
    get_netex_text,
    parse_multilingual_string,
    parse_versioned_ref,
)

log = get_logger()


def parse_tariff(elem: _Element) -> Tariff | None:
    """
    Parse a single Tariff element
    """
    tariff_id = elem.get("id")
    tariff_version = elem.get("version")
    name = parse_multilingual_string(elem, "Name")

    if not tariff_id or not tariff_version or not name:
        log.warning("Tariff missing required fields")
        return None

    operator_ref = parse_versioned_ref(elem, "OperatorRef")
    line_ref = parse_versioned_ref(elem, "LineRef")
    type_of_tariff_ref = parse_versioned_ref(elem, "TypeOfTariffRef")

    return Tariff(
        id=tariff_id,
        version=tariff_version,
        validityConditions=[],  # Parse validity conditions
        Name=name,
        OperatorRef=operator_ref,
        LineRef=line_ref,
        TypeOfTariffRef=type_of_tariff_ref,
        TariffBasis=get_netex_text(elem, "TariffBasis"),
        fareStructureElements=[],  # Parse fare structure elements
    )
