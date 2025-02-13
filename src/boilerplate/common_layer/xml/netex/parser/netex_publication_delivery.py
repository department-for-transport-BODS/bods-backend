"""
Parser for Top Level PublicationDelivery
"""

from pathlib import Path

from lxml import etree
from structlog.stdlib import get_logger

from ...utils import get_tag_name, unload_element
from ..models import PublicationDeliveryStructure
from .netex_data_objects import parse_data_objects
from .netex_publication_request import parse_publication_request
from .netex_utility import parse_multilingual_string, parse_timedelta, parse_timestamp

log = get_logger()

NETEX_NS = "http://www.netex.org.uk/netex"


def parse_netex(filename: Path) -> PublicationDeliveryStructure:
    """
    Parse NeTEx PublicationDelivery XML iteratively with modular parsing functions.
    """
    context = etree.iterparse(
        filename, events=("start", "end"), remove_blank_text=True, remove_comments=True
    )

    event, root = next(context)
    if root.tag != f"{{{NETEX_NS}}}PublicationDelivery":
        raise ValueError("Root element must be PublicationDelivery")

    version = root.get("version")
    publication_timestamp = None
    participant_ref = None
    publication_request = None
    description = None
    refresh_interval = None
    data_objects = []

    # Parse remaining elements
    for event, elem in context:
        if event != "end":
            continue

        try:
            tag = get_tag_name(elem)

            match tag:
                case "PublicationTimestamp":
                    publication_timestamp = parse_timestamp(elem)
                case "ParticipantRef":
                    participant_ref = elem.text
                case "PublicationRequest":
                    publication_request = parse_publication_request(elem)
                case "PublicationRefreshInterval":
                    refresh_interval = parse_timedelta(elem)
                case "Description":
                    description = parse_multilingual_string(elem)
                case "dataObjects":
                    data_objects = parse_data_objects(elem)
                case _:
                    log.warning("Unexpected Tag in PublicationDelivery", tag=tag)
        finally:
            unload_element(elem)
    if publication_timestamp is None:
        raise ValueError("PublicationTimestamp is Required")
    if participant_ref is None:
        raise ValueError("ParticipantRef is Required")

    return PublicationDeliveryStructure(
        version=version if version else "v1.0",
        PublicationTimestamp=publication_timestamp,
        ParticipantRef=participant_ref,
        PublicationRequest=publication_request,
        PublicationRefreshInterval=refresh_interval,
        Description=description,
        dataObjects=data_objects,
    )
