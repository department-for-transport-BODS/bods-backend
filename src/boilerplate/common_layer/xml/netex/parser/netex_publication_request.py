"""
PublicationRequestParsing
"""

from datetime import datetime

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import get_tag_name
from ..models import (
    MultilingualString,
    NetworkFrameRequestPolicyStructure,
    NetworkFrameSubscriptionPolicyStructure,
    NetworkFrameTopicStructure,
    PublicationRequestStructure,
)
from .netex_network_frame import parse_network_frame_topic
from .netex_utility import parse_multilingual_string, parse_timestamp

log = get_logger()


def parse_topics(elem: _Element) -> list[NetworkFrameTopicStructure] | None:
    """
    Parse topics element containing NetworkFrameTopics.
    """
    topics: list[NetworkFrameTopicStructure] = []

    for child in elem:
        if get_tag_name(child) == "NetworkFrameTopic":
            topics.append(parse_network_frame_topic(child))
        child.clear()

    return topics if topics else None


def parse_publication_request(elem: _Element) -> PublicationRequestStructure:
    """
    Parse PublicationRequest element.
    """
    version = elem.get("version", "1.0")
    request_timestamp: datetime | None = None
    participant_ref: str | None = None
    description: MultilingualString | None = None
    topics_list: list[NetworkFrameTopicStructure] | None = None
    request_policy: NetworkFrameRequestPolicyStructure | None = None
    subscription_policy: NetworkFrameSubscriptionPolicyStructure | None = None

    for child in elem:
        tag = get_tag_name(child)

        match tag:
            case "RequestTimestamp":
                request_timestamp = parse_timestamp(child)
            case "ParticipantRef":
                participant_ref = child.text
            case "Description":
                description = parse_multilingual_string(child)
            case "topics":
                topics_list = parse_topics(child)
            case "RequestPolicy":
                log.error("Parsing Network Frame Subscription Policy not implemented")
                request_policy = None
            case "SubscriptionPolicy":
                log.error("Parsing Network Frame Subscription Policy not implemented")
                subscription_policy = None
            case _:
                log.warning("Unknown PublicationRequest Tag", tag=tag)
        child.clear()

    return PublicationRequestStructure(
        version=version,
        RequestTimestamp=request_timestamp,
        ParticipantRef=participant_ref,
        Description=description,
        topics=topics_list,
        RequestPolicy=request_policy,
        SubscriptionPolicy=subscription_policy,
    )
