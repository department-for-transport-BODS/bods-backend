"""
PublicationDelivery -> dataObjects
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name
from ...models import CompositeFrame
from .netex_frame_composite import parse_composite_frame

log = get_logger()


def parse_data_objects(elem: _Element) -> list[CompositeFrame]:
    """
    Parse dataObjects
    """
    frames: list[CompositeFrame] = []

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "CompositeFrame":
                frames.append(parse_composite_frame(child))
            case _:
                log.warning("Unsupported frame type in dataObjects", tag=tag)

    return frames
