"""
Tariff Parsing
"""

from lxml.etree import _Element
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import FareStructureElement, FromToDate, Tariff
from ..netex_types import parse_tariff_basis_type
from ..netex_utility import (
    get_netex_element,
    get_netex_text,
    parse_from_to_date,
    parse_multilingual_string,
    parse_versioned_ref,
)
from .netex_fare_tariff_fare_structure import parse_fare_structure_element

log = get_logger()


def parse_validity_conditions(elem: _Element) -> list[FromToDate]:
    """
    Parse ValidityConditions element containing ValidBetween elements
    """
    validity_conditions: list[FromToDate] = []
    validity_conditions_elem = get_netex_element(elem, "validityConditions")
    if validity_conditions_elem is not None:
        for child in validity_conditions_elem:
            tag = get_tag_name(child)
            if tag == "ValidBetween":
                validity_conditions.append(parse_from_to_date(child))
            else:
                log.warning("Unknown ValidityConditions tag", tag=tag)
            child.clear()

    return validity_conditions


def parse_fare_structure_elements(elem: _Element) -> list[FareStructureElement]:
    """
    Parse fareStructureElements element
    """
    fare_structure_elements: list[FareStructureElement] = []
    fare_structure_elements_elem = get_netex_element(elem, "fareStructureElements")
    if fare_structure_elements_elem is not None:
        for child in fare_structure_elements_elem:
            tag = get_tag_name(child)
            if tag == "FareStructureElement":
                fare_structure_elements.append(parse_fare_structure_element(child))
            else:
                log.warning("Unknown FareStructureElements tag", tag=tag)
            child.clear()

    return fare_structure_elements


def parse_tariff(elem: _Element) -> Tariff:
    """
    Parse Tariff element
    """
    tariff_id = elem.get("id")
    version = elem.get("version")

    if not tariff_id or not version:
        raise ValueError("Missing required id or version in Tariff")

    # Parse required fields
    name = parse_multilingual_string(elem, "Name")
    if name is None:
        name = get_netex_text(elem, "Name")

    operator_ref = parse_versioned_ref(elem, "OperatorRef")

    line_ref = parse_versioned_ref(elem, "LineRef")

    type_of_tariff_ref = parse_versioned_ref(elem, "TypeOfTariffRef")

    tariff_basis = parse_tariff_basis_type(elem)
    validity_conditions = parse_validity_conditions(elem)
    fare_structure_elements = parse_fare_structure_elements(elem)

    return Tariff(
        id=tariff_id,
        version=version,
        validityConditions=validity_conditions,
        Name=name,
        OperatorRef=operator_ref,
        LineRef=line_ref,
        TypeOfTariffRef=type_of_tariff_ref,
        TariffBasis=tariff_basis,
        fareStructureElements=fare_structure_elements,
    )


def parse_tariffs(elem: _Element) -> list[Tariff]:
    """Parse tariffs list element"""
    tariffs: list[Tariff] = []
    for tariff in elem:
        if get_tag_name(tariff) == "Tariff":
            tariffs.append(parse_tariff(tariff))
        else:
            log.warning("Unknown tariffs tag", tag=get_tag_name(tariff))
    return tariffs
