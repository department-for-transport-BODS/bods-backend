"""
SalesOfferPackage
"""

from common_layer.xml.netex.models.fare_frame.netex_sales_offer_package import (
    SalesOfferPackage,
)
from common_layer.xml.utils.xml_utils_tags import get_tag_name
from lxml.etree import _Element
from structlog import get_logger

log = get_logger()


def parse_sales_offer_package(elem: _Element) -> SalesOfferPackage:
    """
    Parse a single SalesOfferPackage element
    """
    sales_offer_package_id = elem.get("id")
    sales_offer_package_version = elem.get("version")

    if not sales_offer_package_id or not sales_offer_package_version:
        log.warning(
            "SalesOfferPackage missing required fields",
            id=sales_offer_package_id,
            version=sales_offer_package_version,
        )
        raise ValueError("Missing required id or version in sales offer package")

    return SalesOfferPackage(
        id=sales_offer_package_id, version=sales_offer_package_version
    )


def parse_sales_offer_packages(elem: _Element) -> list[SalesOfferPackage]:
    """
    Parse a list of SalesOfferPackage elements
    """
    sales_offer_packages: list[SalesOfferPackage] = []
    for child in elem:
        if get_tag_name(child) == "SalesOfferPackage":
            zone = parse_sales_offer_package(child)
            if zone:
                sales_offer_packages.append(zone)
    return sales_offer_packages
