"""
PublicationRequestParsing
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import get_tag_name
from ..models import NetworkFrameTopicStructure, PublicationRequestStructure
from .netex_network_frame import parse_network_frame_topic
from .netex_utility import (
    get_netex_element,
    get_netex_text,
    parse_multilingual_string,
    parse_timestamp,
)

log = get_logger()


def parse_topics(elem: _Element) -> list[NetworkFrameTopicStructure] | None:
    """
    Parse topics element containing NetworkFrameTopics.
    """
    topics: list[NetworkFrameTopicStructure] = []

    for child in elem:
        if get_tag_name(child) == "NetworkFrameTopic":
            log.info("There is a child")
            topics.append(parse_network_frame_topic(child))
    log.debug("Parsed Topics", count=len(topics))
    return topics if topics else None


def parse_publication_request(elem: _Element) -> PublicationRequestStructure:
    """
    Parse PublicationRequest element with namespace-aware child iteration.
    """
    version = elem.get("version", "1.0")
    request_timestamp = parse_timestamp(elem, "RequestTimestamp")
    participant_ref = get_netex_text(elem, "ParticipantRef")
    description = parse_multilingual_string(elem, "Description")
    topics = []
    topics_xml = get_netex_element(elem, "topics")
    if topics_xml is not None:
        topics = parse_topics(topics_xml)
    request_policy = get_netex_element(elem, "RequestPolicy")
    if request_policy:
        log.debug("Parsing Network Frame Subscription Policy not implemented")
        request_policy = None
    subscription_policy = get_netex_element(elem, "SubscriptionPolicy")
    if subscription_policy:
        log.debug("Parsing Network Frame Subscription Policy not implemented")
        subscription_policy = None

    return PublicationRequestStructure(
        version=version,
        RequestTimestamp=request_timestamp,
        ParticipantRef=participant_ref,
        Description=description,
        topics=topics,
        RequestPolicy=None,
        SubscriptionPolicy=None,
    )
