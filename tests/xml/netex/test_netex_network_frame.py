"""
Test NetworkFrame Parsing
"""

from datetime import UTC, datetime

import pytest
from common_layer.xml.netex.models import (
    AvailabilityCondition,
    NetworkFilterByValueStructure,
    NetworkFrameTopicStructure,
    ObjectReferences,
    SelectionValidityConditions,
    VersionedRef,
)
from common_layer.xml.netex.parser import (
    parse_network_filter_by_value,
    parse_network_frame_topic,
    parse_object_references,
)
from lxml.etree import fromstring

from tests.xml.conftest import assert_model_equal


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <objectReferences>
                <OperatorRef version="1.0" ref="noc:BRTB" />
                <LineRef version="1.0" ref="BRTB:PC0003375:3:15" />
            </objectReferences>
            """,
            ObjectReferences(
                OperatorRef=VersionedRef(version="1.0", ref="noc:BRTB"),
                LineRef=VersionedRef(version="1.0", ref="BRTB:PC0003375:3:15"),
            ),
            id="Valid object references",
        ),
        pytest.param(
            """
            <objectReferences>
                <OperatorRef version="2.0" ref="operator1" />
                <LineRef version="2.0" ref="line1" />
                <UnknownRef version="1.0" ref="something" />
            </objectReferences>
            """,
            ObjectReferences(
                OperatorRef=VersionedRef(version="2.0", ref="operator1"),
                LineRef=VersionedRef(version="2.0", ref="line1"),
            ),
            id="Object references with unknown tag",
        ),
    ],
)
def test_parse_object_references(xml_str: str, expected: ObjectReferences) -> None:
    """Test parsing of object references with various inputs."""
    elem = fromstring(xml_str.strip())
    result = parse_object_references(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,error_msg",
    [
        pytest.param(
            """
            <objectReferences>
                <OperatorRef version="1.0" ref="noc:BRTB" />
            </objectReferences>
            """,
            "Missing required references in ObjectReferences",
            id="Missing LineRef",
        ),
        pytest.param(
            """
            <objectReferences>
                <LineRef version="1.0" ref="BRTB:PC0003375:3:15" />
            </objectReferences>
            """,
            "Missing required references in ObjectReferences",
            id="Missing OperatorRef",
        ),
        pytest.param(
            """
            <objectReferences>
            </objectReferences>
            """,
            "Missing required references in ObjectReferences",
            id="Empty object references",
        ),
    ],
)
def test_parse_object_references_errors(xml_str: str, error_msg: str) -> None:
    """Test error cases for object references parsing."""
    elem = fromstring(xml_str.strip())
    with pytest.raises(ValueError, match=error_msg):
        parse_object_references(elem)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <NetworkFilterByValue>
                <objectReferences>
                    <OperatorRef version="1.0" ref="noc:BRTB" />
                    <LineRef version="1.0" ref="BRTB:PC0003375:3:15" />
                </objectReferences>
            </NetworkFilterByValue>
            """,
            NetworkFilterByValueStructure(
                objectReferences=ObjectReferences(
                    OperatorRef=VersionedRef(version="1.0", ref="noc:BRTB"),
                    LineRef=VersionedRef(version="1.0", ref="BRTB:PC0003375:3:15"),
                )
            ),
            id="Valid network filter",
        ),
    ],
)
def test_parse_network_filter_by_value(
    xml_str: str, expected: NetworkFilterByValueStructure
) -> None:
    """Test parsing of network filter with various inputs."""
    elem = fromstring(xml_str.strip())
    result = parse_network_filter_by_value(elem)
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <NetworkFrameTopic>
                <selectionValidityConditions>
                    <AvailabilityCondition version="1.0" id="r1">
                        <FromDate>2019-08-14T00:00:00Z</FromDate>
                        <ToDate>2024-08-14T00:00:00Z</ToDate>
                    </AvailabilityCondition>
                </selectionValidityConditions>
                <TypeOfFrameRef version="1.0" ref="UK:DFT:TypeOfFrame:FXCP"/>
                <NetworkFilterByValue>
                    <objectReferences>
                        <OperatorRef version="1.0" ref="noc:BRTB"/>
                        <LineRef version="1.0" ref="BRTB:PC0003375:3:15"/>
                    </objectReferences>
                </NetworkFilterByValue>
            </NetworkFrameTopic>
            """,
            NetworkFrameTopicStructure(
                selectionValidityConditions=[
                    SelectionValidityConditions(
                        AvailabilityConditions=[
                            AvailabilityCondition(
                                version="1.0",
                                id="r1",
                                FromDate=datetime(2019, 8, 14, 0, 0, tzinfo=UTC),
                                ToDate=datetime(2024, 8, 14, 0, 0, tzinfo=UTC),
                            )
                        ],
                        SimpleAvailabilityConditions=[],
                    )
                ],
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
            ),
            id="Complete network frame topic",
        ),
        pytest.param(
            """
            <NetworkFrameTopic>
                <TypeOfFrameRef version="1.0" ref="UK:DFT:TypeOfFrame:FXCP"/>
            </NetworkFrameTopic>
            """,
            NetworkFrameTopicStructure(
                selectionValidityConditions=[],
                TypeOfFrameRef=VersionedRef(
                    version="1.0", ref="UK:DFT:TypeOfFrame:FXCP"
                ),
                NetworkFilterByValue=[],
            ),
            id="Minimal network frame topic with only TypeOfFrameRef",
        ),
        pytest.param(
            """
            <NetworkFrameTopic>
                <selectionValidityConditions>
                    <AvailabilityCondition version="1.0" id="r1">
                        <FromDate>2019-08-14T00:00:00Z</FromDate>
                    </AvailabilityCondition>
                </selectionValidityConditions>
                <TypeOfFrameRef version="1.0" ref="UK:DFT:TypeOfFrame:FXCP"/>
                <NetworkFilterByValue>
                    <objectReferences>
                        <OperatorRef version="1.0" ref="noc:BRTB"/>
                        <LineRef version="1.0" ref="BRTB:PC0003375:3:15"/>
                    </objectReferences>
                </NetworkFilterByValue>
                <NetworkFilterByValue>
                    <objectReferences>
                        <OperatorRef version="1.0" ref="noc:BRTB2"/>
                        <LineRef version="1.0" ref="BRTB:PC0003376:3:15"/>
                    </objectReferences>
                </NetworkFilterByValue>
            </NetworkFrameTopic>
            """,
            NetworkFrameTopicStructure(
                selectionValidityConditions=[
                    SelectionValidityConditions(
                        AvailabilityConditions=[
                            AvailabilityCondition(
                                version="1.0",
                                id="r1",
                                FromDate=datetime(2019, 8, 14, 0, 0, tzinfo=UTC),
                                ToDate=None,
                            )
                        ],
                        SimpleAvailabilityConditions=[],
                    )
                ],
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
                    ),
                    NetworkFilterByValueStructure(
                        objectReferences=ObjectReferences(
                            OperatorRef=VersionedRef(version="1.0", ref="noc:BRTB2"),
                            LineRef=VersionedRef(
                                version="1.0", ref="BRTB:PC0003376:3:15"
                            ),
                        )
                    ),
                ],
            ),
            id="Network frame topic with multiple NetworkFilterByValue elements",
        ),
        pytest.param(
            """
            <NetworkFrameTopic>
                <UnknownTag>Some content</UnknownTag>
                <TypeOfFrameRef version="1.0" ref="UK:DFT:TypeOfFrame:FXCP"/>
            </NetworkFrameTopic>
            """,
            NetworkFrameTopicStructure(
                selectionValidityConditions=[],
                TypeOfFrameRef=VersionedRef(
                    version="1.0", ref="UK:DFT:TypeOfFrame:FXCP"
                ),
                NetworkFilterByValue=[],
            ),
            id="Network frame topic with unknown tag",
        ),
    ],
)
def test_parse_network_frame_topic(
    xml_str: str, expected: NetworkFrameTopicStructure
) -> None:
    """Test parsing of network frame topic with various inputs."""
    elem = fromstring(xml_str.strip())
    result = parse_network_frame_topic(elem)
    assert_model_equal(result, expected)
