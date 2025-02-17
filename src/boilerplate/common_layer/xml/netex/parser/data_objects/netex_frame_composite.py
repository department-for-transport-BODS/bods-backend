"""
CompositeFrame
"""

from common_layer.xml.netex.parser.data_objects.netex_frame_defaults import (
    parse_frame_defaults,
)
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name, parse_xml_attribute
from ...models import CompositeFrame, FareFrame, FromToDate
from ...models.data_objects.netex_frame_resource import ResourceFrame
from ...models.data_objects.netex_frame_service import ServiceFrame
from ..fare_frame.netex_frame_fare import parse_fare_frame
from ..netex_utility import (
    find_required_netex_element,
    get_netex_element,
    parse_multilingual_string,
    parse_timestamp,
    parse_versioned_ref,
)
from .netex_codespaces import parse_codespaces
from .netex_frame_resource import parse_resource_frame
from .netex_frame_service import parse_service_frame

log = get_logger()


def parse_frames(elem: _Element) -> list[ResourceFrame | ServiceFrame | FareFrame]:
    """
    Parse list of frames
    """
    frames: list[ResourceFrame | ServiceFrame | FareFrame] = []
    for child in elem:
        tag = get_tag_name(child)
        match tag:
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


def parse_composite_frame(elem: _Element) -> CompositeFrame:
    """
    Parse a CompositeFrame
    """
    # Parse attributes
    version = parse_xml_attribute(elem, "version")
    if version is None:
        raise ValueError("Missing Version")
    frame_id = parse_xml_attribute(elem, "id")
    if frame_id is None:
        raise ValueError("Missing Frame ID")
    data_source_ref = parse_xml_attribute(elem, "dataSourceRef")
    if data_source_ref is None:
        raise ValueError("Missing DatasourceRef")
    responsibility_set_ref = parse_xml_attribute(elem, "responsibilitySetRef")
    if responsibility_set_ref is None:
        raise ValueError("Missing Responisilbity set ref")
    valid_between = FromToDate(
        FromDate=parse_timestamp(elem, "FromDate"),
        ToDate=parse_timestamp(elem, "ToDate"),
    )

    name = parse_multilingual_string(elem, "Name")
    if name is None:
        raise ValueError("Missing Name")

    # Parse FrameDefaults
    frame_defaults = None
    frame_defaults_elem = get_netex_element(elem, "FrameDefaults")
    if frame_defaults_elem is not None:
        frame_defaults = parse_frame_defaults(frame_defaults_elem)

    frames = parse_frames(find_required_netex_element(elem, "frames"))

    codespaces = []
    codespaces_elem = get_netex_element(elem, "codespaces")
    if codespaces_elem is not None:
        codespaces = parse_codespaces(codespaces_elem)
    return CompositeFrame(
        version=version,
        id=frame_id,
        dataSourceRef=data_source_ref,
        responsibilitySetRef=responsibility_set_ref,
        ValidBetween=valid_between,
        Name=name,
        Description=parse_multilingual_string(elem, "Description"),
        TypeOfFrameRef=parse_versioned_ref(elem, "TypeOfFrameRef"),
        codespaces=codespaces,
        FrameDefaults=frame_defaults,
        frames=frames,
    )
