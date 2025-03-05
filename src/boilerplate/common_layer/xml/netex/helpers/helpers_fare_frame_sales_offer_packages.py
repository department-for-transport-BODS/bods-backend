"""
FareZone Helpers
"""

from ..models import FareFrame, SalesOfferPackage


def get_sales_offer_packages(frames: list[FareFrame]) -> list[SalesOfferPackage]:
    """
    Get a list of sales offer packages across fare frames
    """

    return [
        sop
        for frame in frames
        if frame.salesOfferPackages
        for sop in frame.salesOfferPackages
    ]
