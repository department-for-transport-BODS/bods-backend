"""
PublicationDelivery -> dataObjects
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import CompositeFrame, FareFrame
from ..fare_frame.netex_frame_fare import parse_fare_frame
from .netex_frame_composite import parse_composite_frame

log = get_logger()


def parse_data_objects(elem: _Element) -> list[CompositeFrame | FareFrame]:
    """
    Parse dataObjects
    """
    frames: list[CompositeFrame | FareFrame] = []

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "CompositeFrame":
                frames.append(parse_composite_frame(child))
            case "FareFrame":
                fare_frame = parse_fare_frame(child)
                if fare_frame:
                    frames.append(fare_frame)
            case _:
                log.warning("Unsupported frame type in dataObjects", tag=tag)

    return frames
