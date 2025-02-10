"""
Parse TXC Stop Point Classification
"""

from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_element_text
from ...models import (
    STOP_CLASSIFICATION_STOP_TYPE_MAPPING,
    StopClassificationStructure,
    TXCStopTypeT,
)
from .parse_stop_point_off_street import parse_off_street_structure
from .parse_stop_point_on_street import parse_on_street_structure

log = get_logger()


def parse_stop_classification_structure(
    stop_classification_xml: _Element,
) -> StopClassificationStructure | None:
    """
    StopPoints -> StopPoint -> StopClassification
    """
    stop_type = get_element_text(stop_classification_xml, "StopType")
    if not stop_type:
        log.warning("Missing StopType")
        return None

    # Map the stop type if it's in our mapping
    mapped_stop_type = STOP_CLASSIFICATION_STOP_TYPE_MAPPING.get(stop_type, stop_type)

    # Now validate against TXCStopTypeT
    if mapped_stop_type not in get_args(TXCStopTypeT):
        log.warning(
            "Invalid StopType", stop_type=stop_type, mapped_stop_type=mapped_stop_type
        )
        return None

    # Try parsing OnStreet first
    on_street_xml = stop_classification_xml.find("OnStreet")
    if on_street_xml is not None:
        on_street = parse_on_street_structure(on_street_xml)
        if on_street:
            return StopClassificationStructure(
                StopType=cast(TXCStopTypeT, mapped_stop_type),
                OnStreet=on_street,
                OffStreet=None,
            )

    # If no OnStreet, try OffStreet
    off_street_xml = stop_classification_xml.find("OffStreet")
    if off_street_xml is not None:
        off_street = parse_off_street_structure(off_street_xml)
        if off_street:
            return StopClassificationStructure(
                StopType=cast(TXCStopTypeT, mapped_stop_type),
                OffStreet=off_street,
                OnStreet=None,
            )

    log.warning(
        "Missing both OnStreet and OffStreet sections",
        stop_classification_xml=stop_classification_xml,
    )
    return None
