"""
PublicationDelivery -> dataObjects
"""

from common_layer.xml.utils import get_tag_name
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import CompositeFrame, FareFrame, ResourceFrame, ServiceFrame
from ..fare_frame.netex_frame_fare import parse_fare_frame
from .netex_frame_composite import parse_composite_frame
from .netex_frame_resource import parse_resource_frame
from .netex_frame_service import parse_service_frame

log = get_logger()


def parse_frames(
    elem: _Element,
) -> list[CompositeFrame | ResourceFrame | ServiceFrame | FareFrame]:
    """
    Parse list of frames
    """
    frames: list[CompositeFrame | ResourceFrame | ServiceFrame | FareFrame] = []
    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "CompositeFrame":
                frames.append(parse_composite_frame(child))
            case "ResourceFrame":
                frames.append(parse_resource_frame(child))
            case "ServiceFrame":
                frames.append(parse_service_frame(child))
            case "FareFrame":
                fare_frame = parse_fare_frame(child)
                if fare_frame:
                    frames.append(fare_frame)
            case _:
                log.warning("Unsupported frame type", tag=tag)
    return frames
