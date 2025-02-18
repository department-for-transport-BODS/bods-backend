"""
Parser for Top Level PublicationDelivery
"""

from io import BytesIO
from pathlib import Path

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import load_xml_tree, parse_xml_attribute
from ..models import PublicationDeliveryStructure
from .data_objects.netex_frame_composite import parse_frames
from .netex_constants import NETEX_NS
from .netex_publication_request import parse_publication_request
from .netex_utility import (
    get_netex_element,
    get_netex_text,
    parse_multilingual_string,
    parse_timedelta,
    parse_timestamp,
)

log = get_logger()


def parse_publication_delivery(elem: _Element) -> PublicationDeliveryStructure:
    """
    Parse PublicationDelivery element from loaded XML tree.
    """
    # Get required elements
    publication_timestamp = parse_timestamp(elem, "PublicationTimestamp")
    if publication_timestamp is None:
        raise ValueError("PublicationTimestamp is Required")

    participant_ref = get_netex_text(elem, "ParticipantRef")
    if participant_ref is None:
        raise ValueError("ParticipantRef is Required")

    version = parse_xml_attribute(elem, "version") or "v1.0"

    # Get optional elements
    publication_request_elem = get_netex_element(elem, "PublicationRequest")
    publication_request = (
        parse_publication_request(publication_request_elem)
        if publication_request_elem is not None
        else None
    )

    refresh_interval = parse_timedelta(elem, "PublicationRefreshInterval")

    description = parse_multilingual_string(elem, "Description")

    data_objects_elem = get_netex_element(elem, "dataObjects")
    data_objects = (
        parse_frames(data_objects_elem) if data_objects_elem is not None else []
    )

    return PublicationDeliveryStructure(
        version=version,
        PublicationTimestamp=publication_timestamp,
        ParticipantRef=participant_ref,
        PublicationRequest=publication_request,
        PublicationRefreshInterval=refresh_interval,
        Description=description,
        dataObjects=data_objects,
    )


def parse_netex(filename: Path | BytesIO) -> PublicationDeliveryStructure:
    """
    Parse NeTEx file by first loading the tree then processing PublicationDelivery.
    """
    tree = load_xml_tree(filename)
    root = tree.getroot()

    if root.tag != f"{{{NETEX_NS}}}PublicationDelivery":
        raise ValueError("Root element must be PublicationDelivery")

    return parse_publication_delivery(root)
