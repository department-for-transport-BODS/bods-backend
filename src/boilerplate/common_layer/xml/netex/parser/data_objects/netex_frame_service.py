"""
ServiceFrame
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name, parse_xml_attribute
from ...models import ServiceFrame
from ...models.data_objects.netex_frame_service import Line, ScheduledStopPoint
from ..netex_types import parse_line_type
from ..netex_utility import (
    find_required_netex_element,
    get_netex_text,
    parse_multilingual_string,
    parse_versioned_ref,
)

log = get_logger()


def parse_line(elem: _Element) -> Line | None:
    """
    Parse a single Line element
    """
    line_id = parse_xml_attribute(elem, "id")
    line_version = parse_xml_attribute(elem, "version")
    name = parse_multilingual_string(elem, "Name")
    public_code = get_netex_text(elem, "PublicCode")
    private_code = get_netex_text(elem, "PrivateCode")
    operator_ref = parse_versioned_ref(elem, "OperatorRef")
    line_type = parse_line_type(elem)

    if not line_id or not line_version or not name:
        log.warning(
            "Line Missing items, skipping",
            id=line_id,
            version=line_version,
            name=name,
        )
        return None

    return Line(
        id=line_id,
        version=line_version,
        Name=name,
        Description=parse_multilingual_string(elem, "Description"),
        PublicCode=public_code,
        PrivateCode=private_code,
        OperatorRef=operator_ref,
        LineType=line_type,
    )


def parse_lines(elem: _Element) -> list[Line]:
    """
    Parse a list of Line elements
    """
    lines: list[Line] = []
    for child in elem:
        if get_tag_name(child) == "Line":
            line = parse_line(child)
            if line:
                lines.append(line)
    return lines


def parse_scheduled_stop_point(elem: _Element) -> ScheduledStopPoint | None:
    """
    Parse a single ScheduledStopPoint element
    """
    stop_id = parse_xml_attribute(elem, "id")
    stop_version = parse_xml_attribute(elem, "version")
    name = parse_multilingual_string(elem, "Name")

    if not stop_id or not stop_version:
        log.warning("ScheduledStopPoint missing required fields")
        return None

    return ScheduledStopPoint(id=stop_id, version=stop_version, Name=name)


def parse_scheduled_stop_points(elem: _Element) -> list[ScheduledStopPoint]:
    """
    Parse a list of ScheduledStopPoint elements
    """
    stop_points: list[ScheduledStopPoint] = []
    for child in elem:
        if get_tag_name(child) == "ScheduledStopPoint":
            stop_point = parse_scheduled_stop_point(child)
            if stop_point:
                stop_points.append(stop_point)
    return stop_points


def parse_service_frame(elem: _Element) -> ServiceFrame:
    """
    Parse a ServiceFrame containing service-related definitions including
    lines and scheduled stop points
    """
    # Parse required attributes
    version = parse_xml_attribute(elem, "version")
    if version is None:
        raise ValueError("Missing Version")

    frame_id = parse_xml_attribute(elem, "id")
    if frame_id is None:
        raise ValueError("Missing Frame ID")

    data_source_ref = parse_xml_attribute(elem, "dataSourceRef")
    if data_source_ref is None:
        raise ValueError("Missing DataSourceRef")

    responsibility_set_ref = parse_xml_attribute(elem, "responsibilitySetRef")
    if responsibility_set_ref is None:
        raise ValueError("Missing ResponsibilitySetRef")

    # Parse type of frame reference
    type_of_frame_ref = parse_versioned_ref(elem, "TypeOfFrameRef")
    if type_of_frame_ref is None:
        raise ValueError("Missing TypeOfFrameRef")

    # Parse lists
    lines = parse_lines(find_required_netex_element(elem, "lines"))
    stop_points = parse_scheduled_stop_points(
        find_required_netex_element(elem, "scheduledStopPoints")
    )

    return ServiceFrame(
        version=version,
        id=frame_id,
        dataSourceRef=data_source_ref,
        responsibilitySetRef=responsibility_set_ref,
        Description=parse_multilingual_string(elem, "Description"),
        TypeOfFrameRef=type_of_frame_ref,
        lines=lines,
        scheduledStopPoints=stop_points,
    )
