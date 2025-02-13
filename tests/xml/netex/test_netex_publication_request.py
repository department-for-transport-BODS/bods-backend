"""
Test Parsing Publication Requests
"""

from datetime import datetime, timezone

import pytest
from common_layer.xml.netex.models import (
    MultilingualString,
    NetworkFilterByValueStructure,
    NetworkFrameTopicStructure,
    ObjectReferences,
    PublicationRequestStructure,
    VersionedRef,
)
from common_layer.xml.netex.parser import parse_publication_request, parse_topics
from lxml.etree import fromstring

from tests.xml.conftest import assert_model_equal

UTC = timezone.utc


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <topics>
                <NetworkFrameTopic>
                    <TypeOfFrameRef version="1.0" ref="UK:DFT:TypeOfFrame:FXCP"/>
                    <NetworkFilterByValue>
                        <objectReferences>
                            <OperatorRef version="1.0" ref="noc:BRTB"/>
                            <LineRef version="1.0" ref="BRTB:PC0003375:3:15"/>
                        </objectReferences>
                    </NetworkFilterByValue>
                </NetworkFrameTopic>
            </topics>
            """,
            [
                NetworkFrameTopicStructure(
                    selectionValidityConditions=[],
                    TypeOfFrameRef=VersionedRef(
                        version="1.0", ref="UK:DFT:TypeOfFrame:FXCP"
                    ),
                    NetworkFilterByValue=[
                        NetworkFilterByValueStructure(
                            objectReferences=ObjectReferences(
                                OperatorRef=VersionedRef(version="1.0", ref="noc:BRTB"),
                                LineRef=VersionedRef(
                                    version="1.0", ref="BRTB:PC0003375:3:15"
                                ),
                            )
                        )
                    ],
                )
            ],
            id="Single network frame topic",
        ),
        pytest.param(
            """
            <topics>
                <NetworkFrameTopic>
                    <TypeOfFrameRef version="1.0" ref="UK:DFT:TypeOfFrame:FXCP1"/>
                </NetworkFrameTopic>
                <NetworkFrameTopic>
                    <TypeOfFrameRef version="1.0" ref="UK:DFT:TypeOfFrame:FXCP2"/>
                </NetworkFrameTopic>
            </topics>
            """,
            [
                NetworkFrameTopicStructure(
                    selectionValidityConditions=[],
                    TypeOfFrameRef=VersionedRef(
                        version="1.0", ref="UK:DFT:TypeOfFrame:FXCP1"
                    ),
                    NetworkFilterByValue=[],
                ),
                NetworkFrameTopicStructure(
                    selectionValidityConditions=[],
                    TypeOfFrameRef=VersionedRef(
                        version="1.0", ref="UK:DFT:TypeOfFrame:FXCP2"
                    ),
                    NetworkFilterByValue=[],
                ),
            ],
            id="Multiple network frame topics",
        ),
        pytest.param(
            """
            <topics>
                <OtherTag>Some content</OtherTag>
            </topics>
            """,
            None,
            id="No network frame topics",
        ),
        pytest.param(
            """
            <topics/>
            """,
            None,
            id="Empty topics element",
        ),
    ],
)
def test_parse_topics(
    xml_str: str, expected: list[NetworkFrameTopicStructure] | None
) -> None:
    """Test parsing of topics element with various inputs."""
    elem = fromstring(xml_str.strip())
    result = parse_topics(elem)
    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert len(result) == len(expected)
        for res, exp in zip(result, expected):
            assert_model_equal(res, exp)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <PublicationRequest version="1.0">
                <RequestTimestamp>2024-02-13T12:00:00Z</RequestTimestamp>
                <ParticipantRef>PARTICIPANT_1</ParticipantRef>
                <Description>Test request</Description>
                <topics>
                    <NetworkFrameTopic>
                        <TypeOfFrameRef version="1.0" ref="UK:DFT:TypeOfFrame:FXCP"/>
                    </NetworkFrameTopic>
                </topics>
            </PublicationRequest>
            """,
            PublicationRequestStructure(
                version="1.0",
                RequestTimestamp=datetime(2024, 2, 13, 12, 0, tzinfo=UTC),
                ParticipantRef="PARTICIPANT_1",
                Description=MultilingualString(value="Test request"),
                topics=[
                    NetworkFrameTopicStructure(
                        selectionValidityConditions=[],
                        TypeOfFrameRef=VersionedRef(
                            version="1.0", ref="UK:DFT:TypeOfFrame:FXCP"
                        ),
                        NetworkFilterByValue=[],
                    )
                ],
                RequestPolicy=None,
                SubscriptionPolicy=None,
            ),
            id="Complete publication request",
        ),
        pytest.param(
            """
            <PublicationRequest>
                <RequestTimestamp>2024-02-13T12:00:00Z</RequestTimestamp>
                <ParticipantRef>PARTICIPANT_1</ParticipantRef>
            </PublicationRequest>
            """,
            PublicationRequestStructure(
                version="1.0",
                RequestTimestamp=datetime(2024, 2, 13, 12, 0, tzinfo=UTC),
                ParticipantRef="PARTICIPANT_1",
                Description=None,
                topics=None,
                RequestPolicy=None,
                SubscriptionPolicy=None,
            ),
            id="Minimal publication request",
        ),
        pytest.param(
            """
            <PublicationRequest version="2.0">
                <RequestTimestamp>2024-02-13T12:00:00Z</RequestTimestamp>
                <ParticipantRef>PARTICIPANT_1</ParticipantRef>
                <UnknownTag>Some content</UnknownTag>
                <RequestPolicy>Some policy</RequestPolicy>
                <SubscriptionPolicy>Some policy</SubscriptionPolicy>
            </PublicationRequest>
            """,
            PublicationRequestStructure(
                version="2.0",
                RequestTimestamp=datetime(2024, 2, 13, 12, 0, tzinfo=UTC),
                ParticipantRef="PARTICIPANT_1",
                Description=None,
                topics=None,
                RequestPolicy=None,
                SubscriptionPolicy=None,
            ),
            id="Publication request with unimplemented policies",
        ),
    ],
)
def test_parse_publication_request(
    xml_str: str, expected: PublicationRequestStructure
) -> None:
    """Test parsing of publication request with various inputs."""
    elem = fromstring(xml_str.strip())
    result = parse_publication_request(elem)
    assert_model_equal(result, expected)
