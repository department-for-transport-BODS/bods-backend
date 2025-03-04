"""
Networkframe Topic
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import get_tag_name
from ..models import (
    NetworkFilterByValueStructure,
    NetworkFrameTopicStructure,
    SelectionValidityConditions,
    VersionedRef,
)
from .netex_references import parse_object_references
from .netex_selection_validity import parse_selection_validity_conditions
from .netex_utility import parse_versioned_ref

log = get_logger()


def parse_network_filter_by_value(elem: _Element) -> NetworkFilterByValueStructure:
    """Parse NetworkFilterByValue element."""
    object_refs = None

    for child in elem:
        if get_tag_name(child) == "objectReferences":
            object_refs = parse_object_references(child)
        child.clear()

    return NetworkFilterByValueStructure(objectReferences=object_refs)


def parse_network_frame_topic(elem: _Element) -> NetworkFrameTopicStructure:
    """Parse NetworkFrameTopic element."""
    selection_validity_conditions: list[SelectionValidityConditions] = []
    type_of_frame_ref: VersionedRef | None = parse_versioned_ref(elem, "TypeOfFrameRef")
    network_filter_by_value: list[NetworkFilterByValueStructure] = []

    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "selectionValidityConditions":
                selection_validity_conditions.append(
                    parse_selection_validity_conditions(child)
                )
            case "NetworkFilterByValue":
                network_filter_by_value.append(parse_network_filter_by_value(child))
            case _:
                pass
        child.clear()

    return NetworkFrameTopicStructure(
        selectionValidityConditions=selection_validity_conditions,
        TypeOfFrameRef=type_of_frame_ref,
        NetworkFilterByValue=network_filter_by_value,
    )
