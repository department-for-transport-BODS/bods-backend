"""
Type Parsing Helpers
"""

from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import get_element_text
from ..models import (
    TIMING_STATUS_MAPPING,
    JourneyPatternVehicleDirectionT,
    TimingStatusT,
)

log = get_logger()


def parse_jp_direction(elem: _Element) -> JourneyPatternVehicleDirectionT | None:
    """
    Parse a JourneyPatternVehicleDirectionT from a TXC XML element
    """
    text = get_element_text(elem, "Direction")

    original_text = text
    text = text.strip() if text else text

    if text != original_text:
        log.info(
            "Stripped whitespace from JourneyPatternVehicleDirectionT",
            original=original_text,
            cleaned=text,
        )

    if text in get_args(JourneyPatternVehicleDirectionT):
        return cast(JourneyPatternVehicleDirectionT, text)

    log.warning("Unknown JourneyPatternVehicleDirectionT Type", text=text)
    return None


def parse_timing_status(elem: _Element) -> TimingStatusT | None:
    """
    Parse a TimingStatus used in:
        - Custom Stop Points (i.e. Naptan Model for Stops)
        - JourneyPatternStopUsage in JourneyPatternSections
    """
    text = get_element_text(elem, "TimingStatus")
    if not text:
        return None

    timing_status = TIMING_STATUS_MAPPING.get(text)
    if timing_status is not None:
        return timing_status

    if text in get_args(TimingStatusT):
        log.warning("Timing Status not in Mapping but is in the type list", value=text)
        return cast(TimingStatusT, text)

    log.warning("Invalid Timing Status", value=text)
    return None
