"""
Test NetworkFrame Parsing
"""

from datetime import UTC, datetime

import pytest
from common_layer.xml.netex.models import (
    AvailabilityCondition,
    NetworkFilterByValueStructure,
    NetworkFrameTopicStructure,
    SelectionValidityConditions,
    VersionedRef,
)
from common_layer.xml.netex.models.netex_references import ObjectReferences
from common_layer.xml.netex.parser import (
    parse_network_filter_by_value,
    parse_network_frame_topic,
)

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


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
    elem = parse_xml_str_as_netex(xml_str)
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
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_network_frame_topic(elem)
    assert_model_equal(result, expected)
