"""
Pricing Parameter Set Parsing
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models.fare_frame.netex_frame_fare import PriceUnit, PricingParameterSet
from ..netex_utility import (
    get_netex_element,
    get_netex_int,
    get_netex_text,
    parse_multilingual_string,
)

log = get_logger()


def parse_price_unit(elem: _Element) -> PriceUnit:
    """
    Parse PriceUnit element
    """
    unit_id = elem.get("id")
    version = elem.get("version")

    if not unit_id or not version:
        raise ValueError("Missing required id or version in PriceUnit")

    name = parse_multilingual_string(elem, "Name")
    private_code = get_netex_text(elem, "PrivateCode")
    precision = get_netex_int(elem, "Precision")

    return PriceUnit(
        id=unit_id,
        version=version,
        Name=name,
        PrivateCode=private_code,
        Precision=precision,
    )


def parse_pricing_parameter_set(elem: _Element) -> PricingParameterSet:
    """
    Parse PricingParameterSet element
    """
    set_id = elem.get("id")
    version = elem.get("version")

    if not set_id or not version:
        raise ValueError("Missing required id or version in PricingParameterSet")

    price_units: list[PriceUnit] = []
    price_units_elem = get_netex_element(elem, "priceUnits")

    if price_units_elem is not None:
        for child in price_units_elem:
            tag = get_tag_name(child)
            if tag == "PriceUnit":
                price_units.append(parse_price_unit(child))
            else:
                log.warning("Unknown priceUnits tag", tag=tag)
            child.clear()

    if not price_units:
        raise ValueError("PricingParameterSet must contain at least one PriceUnit")

    return PricingParameterSet(
        id=set_id,
        version=version,
        priceUnits=price_units,
    )
