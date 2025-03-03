"""
Type Parsing Helpers
"""

from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import get_element_text
from ..models import JourneyPatternVehicleDirectionT

log = get_logger()


def parse_jp_direction(elem: _Element) -> JourneyPatternVehicleDirectionT | None:
    """
    Parse a JourneyPatternVehicleDirectionT from a TXC XML element
    """
    text = get_element_text(elem, "Direction")
    if text in get_args(JourneyPatternVehicleDirectionT):
        return cast(JourneyPatternVehicleDirectionT, text)
    log.warning("Unknown JourneyPatternVehicleDirectionT Type", text=text)
    return None
