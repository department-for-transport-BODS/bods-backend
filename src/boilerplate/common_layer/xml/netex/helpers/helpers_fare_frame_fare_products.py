"""
FareFrame Helpers
"""

from structlog.stdlib import get_logger

from ..models import PreassignedFareProduct, PreassignedFareProductTypeT

log = get_logger()


def get_product_types(
    fare_products: list[PreassignedFareProduct],
) -> list[PreassignedFareProductTypeT]:
    """
    Get ProductType list from PreassignedFareProduct list
    """
    product_types: list[PreassignedFareProductTypeT] = []
    for product in fare_products:
        if product.ProductType is not None:
            product_types.append(product.ProductType)
    return product_types


def get_product_names(
    fare_products: list[PreassignedFareProduct],
) -> list[str]:
    """
    Get Product Names from PreassignedFareProduct list
    """
    product_names: list[str] = []
    for product in fare_products:
        if product.Name is not None:
            product_names.append(product.Name.value)
    return product_names
