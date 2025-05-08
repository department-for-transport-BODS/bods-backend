"""
Various Counts
"""

from pydantic import BaseModel

from ..models import CompositeFrame, FareFrame, ResourceFrame, ServiceFrame
from ..models.fare_frame.netex_fare_preassigned import PreassignedFareProduct
from ..models.fare_frame.netex_fare_tariff import Tariff
from ..models.netex_types import PreassignedFareProductTypeT
from .helpers_fare_frame_fare_products import get_product_types
from .helpers_fare_frame_sales_offer_packages import get_sales_offer_packages
from .helpers_fare_frame_tariff import get_user_types
from .helpers_fare_frame_zones import get_fare_zones


class SortedFrames(BaseModel):
    """
    Sorted Frames
    """

    service_frames: list[ServiceFrame] = []
    resource_frames: list[ResourceFrame] = []
    fare_frames: list[FareFrame] = []
    composite_frames: list[CompositeFrame] = []


def sort_frames(
    frames: list[CompositeFrame | ResourceFrame | ServiceFrame | FareFrame],
) -> SortedFrames:
    """
    Sorts frames into their respective types using pattern matching. Handles both top-level frames
    and frames nested within CompositeFrames.
    """
    sorted_frames = SortedFrames()
    frames_to_process = list(frames)

    while frames_to_process:
        frame = frames_to_process.pop()
        match frame:
            case CompositeFrame():
                frames_to_process.extend(frame.frames)
                sorted_frames.composite_frames.append(frame)
            case ServiceFrame():
                sorted_frames.service_frames.append(frame)
            case ResourceFrame():
                sorted_frames.resource_frames.append(frame)
            case FareFrame():
                sorted_frames.fare_frames.append(frame)

    return sorted_frames


def number_of_lines(frames: list[ServiceFrame]) -> int:
    """
    Number of Lines in a Netex Doc
    """
    return sum(frame.numOfLines for frame in frames)


def number_of_fare_zones(frames: list[FareFrame]) -> int:
    """
    Number of Fare Zones
    """
    return len(get_fare_zones(frames))


def number_of_pass_fare_products(fare_products: list[PreassignedFareProduct]) -> int:
    """
    Number of Pass Fare Products
    """
    pass_product_values: list[PreassignedFareProductTypeT] = ["dayPass", "periodPass"]

    fare_product_types = get_product_types(fare_products)

    return len([type for type in fare_product_types if type in pass_product_values])


def number_of_trip_fare_products(fare_products: list[PreassignedFareProduct]) -> int:
    """
    Number of Trip Fare Products
    """
    trip_product_values: list[PreassignedFareProductTypeT] = [
        "singleTrip",
        "dayReturnTrip",
        "periodReturnTrip",
        "timeLimitedSingleTrip",
        "shortTrip",
    ]

    fare_product_types = get_product_types(fare_products)

    return len([type for type in fare_product_types if type in trip_product_values])


def number_of_distinct_user_profiles(tariffs: list[Tariff]) -> int:
    """
    Number of distinct user profiles
    """
    distinct_user_profiles = set(get_user_types(tariffs))

    return len(distinct_user_profiles)


def number_of_sales_offer_packages(frames: list[FareFrame]) -> int:
    """
    Number of sales offer packages
    """
    return len(get_sales_offer_packages(frames))


def number_of_fare_products(
    fare_frames: list[FareFrame],
) -> int:
    """
    Get number of fare products across all Fare Frames
    """
    return sum(frame.numOfFareProducts for frame in fare_frames)
