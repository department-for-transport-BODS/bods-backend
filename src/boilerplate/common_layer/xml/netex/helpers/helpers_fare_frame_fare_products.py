"""
FareFrame Helpers
"""

from common_layer.xml.netex.models.fare_frame.netex_frame_fare import FareFrame
from structlog.stdlib import get_logger

from ..models import PreassignedFareProduct, PreassignedFareProductTypeT

log = get_logger()


def get_fare_products(fare_frames: list[FareFrame]) -> list[PreassignedFareProduct]:
    """
    Get list of PreassignedFareProducts from Fare Frames
    """
    return [
        product
        for frame in fare_frames
        if frame.fareProducts
        for product in frame.fareProducts
    ]


def get_product_types(
    fare_products: list[PreassignedFareProduct],
) -> list[PreassignedFareProductTypeT]:
    """
    Get ProductType list from PreassignedFareProduct list
    """
    product_types: set[PreassignedFareProductTypeT] = set()
    for product in fare_products:
        if product.ProductType is not None:
            product_types.add(product.ProductType)
    return list(product_types)


def get_product_names(
    fare_products: list[PreassignedFareProduct],
) -> list[str]:
    """
    Get Product Names from PreassignedFareProduct list
    """
    product_names: set[str] = set()
    for product in fare_products:
        if product.Name is not None:
            product_names.add(product.Name.value)
    return list(product_names)
