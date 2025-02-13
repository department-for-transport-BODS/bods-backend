"""
Selection Validity parsing
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import get_tag_name
from ..models import (
    AvailabilityCondition,
    SelectionValidityConditions,
    SimpleAvailabilityCondition,
)
from .netex_utility import parse_timestamp

log = get_logger()


def parse_availability_condition(elem: _Element) -> AvailabilityCondition:
    """Parse AvailabilityCondition element."""
    from_date = None
    to_date = None
    version = elem.get("version", "1.0")
    id_ = elem.get("id", "")

    for child in elem.iterchildren():
        tag = get_tag_name(child)
        match tag:
            case "FromDate":
                from_date = parse_timestamp(child)
                log.info("From data", from_data=from_date)
            case "ToDate":
                to_date = parse_timestamp(child)
            case _:
                if tag:
                    log.warning("Unknown AvailabilityCondition tag", tag=tag)
    elem.clear()

    return AvailabilityCondition(
        version=version,
        id=id_,
        FromDate=from_date,
        ToDate=to_date,
    )


def parse_selection_validity_conditions(elem: _Element) -> SelectionValidityConditions:
    """Parse selectionValidityConditions element."""
    availability_conditions: list[AvailabilityCondition] = []
    simple_availability_conditions: list[SimpleAvailabilityCondition] = []

    for child in elem.iterchildren():
        tag = get_tag_name(child)
        match tag:
            case "AvailabilityCondition":
                condition = parse_availability_condition(child)
                availability_conditions.append(condition)
            case "SimpleAvailabilityCondition":
                log.error("Parsing of SimpleAvailabilityCondition not Implemented")
                child.clear()
            case _:
                if tag:
                    log.warning("Unknown SelectionValidityConditions tag", tag=tag)
                child.clear()

    elem.clear()

    return SelectionValidityConditions(
        AvailabilityConditions=availability_conditions,
        SimpleAvailabilityConditions=simple_availability_conditions,
    )
