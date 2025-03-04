"""
ResourceFrame
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name, parse_xml_attribute
from ...models.data_objects.netex_frame_resource import (
    DataSource,
    Operator,
    ResourceFrame,
)
from ..netex_parsing_helpers import parse_version_and_id
from ..netex_utility import (
    find_required_netex_element,
    get_netex_text,
    parse_multilingual_string,
    parse_versioned_ref,
)
from .netex_codespaces import parse_codespaces

log = get_logger()


def parse_data_sources(elem: _Element) -> list[DataSource]:
    """
    Parse a list of DataSource elements
    """
    data_sources: list[DataSource] = []
    for child in elem:
        if get_tag_name(child) == "DataSource":
            ds_id = parse_xml_attribute(child, "id")
            ds_version = parse_xml_attribute(child, "version")
            email = get_netex_text(child, "Email")
            if not ds_id or not ds_version:
                log.warning(
                    "DataSource missing id or version",
                    id=ds_id,
                    version=ds_version,
                    email=email,
                )
                continue

            data_sources.append(DataSource(id=ds_id, version=ds_version, Email=email))
        else:
            log.warning("Unknown Tag", child=str(child))
    return data_sources


def parse_organisations(elem: _Element) -> list[Operator]:
    """
    Parse a list of organisation elements (currently only Operators)
    """
    organisations: list[Operator] = []
    for child in elem:
        if get_tag_name(child) == "Operator":
            op_id = parse_xml_attribute(child, "id")
            op_version = parse_xml_attribute(child, "version")
            public_code = get_netex_text(child, "PublicCode")
            op_name = parse_multilingual_string(child, "Name")

            if not op_version or not op_id:
                log.warning(
                    "Operator missing required fields, skipping",
                    id=op_id,
                    version=op_version,
                    public_code=public_code,
                    name=op_name,
                )
                continue
            organisations.append(
                Operator(
                    id=op_id, version=op_version, PublicCode=public_code, Name=op_name
                )
            )
    return organisations


def parse_resource_frame(elem: _Element) -> ResourceFrame:
    """
    Parse a ResourceFrame containing resource definitions like codespaces,
    data sources, and organizations
    """
    version, frame_id = parse_version_and_id(elem)

    data_source_ref = parse_xml_attribute(elem, "dataSourceRef")

    # Parse required children
    name = parse_multilingual_string(elem, "Name")

    # Parse lists of resources
    codespaces = parse_codespaces(find_required_netex_element(elem, "codespaces"))
    data_sources = parse_data_sources(find_required_netex_element(elem, "dataSources"))
    organisations = parse_organisations(
        find_required_netex_element(elem, "organisations")
    )

    return ResourceFrame(
        version=version,
        id=frame_id,
        dataSourceRef=data_source_ref,
        responsibilitySetRef=parse_xml_attribute(elem, "responsibilitySetRef"),
        Name=name,
        TypeOfFrameRef=parse_versioned_ref(elem, "TypeOfFrameRef"),
        codespaces=codespaces,
        dataSources=data_sources,
        organisations=organisations,
    )
